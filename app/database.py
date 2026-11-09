import sqlite3
import os
import shutil
import threading
import time
from pathlib import Path
from contextlib import contextmanager

# Detect Vercel serverless environment
IS_VERCEL = bool(os.environ.get("VERCEL"))

# Hosted Turso database (permanent storage). Vercel's Turso integration sets these.
TURSO_URL = os.environ.get("TURSO_DATABASE_URL") or os.environ.get("LIBSQL_URL")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN") or os.environ.get("LIBSQL_AUTH_TOKEN") or ""
USE_TURSO = bool(TURSO_URL)

if USE_TURSO:
    # Local copy of the hosted database, kept in sync with Turso
    REPLICA_DIR = Path("/tmp") if IS_VERCEL else Path(__file__).resolve().parent.parent / "data"
    REPLICA_DIR.mkdir(exist_ok=True)
    DB_PATH = REPLICA_DIR / "turso_replica.db"
elif IS_VERCEL:
    DB_DIR = Path("/tmp")
    DB_PATH = DB_DIR / "dj_microgreens.db"
    # Copy pre-seeded DB if present in repo
    SRC_DB = Path(__file__).resolve().parent.parent / "data" / "dj_microgreens.db"
    if SRC_DB.exists() and not DB_PATH.exists():
        try:
            shutil.copy2(SRC_DB, DB_PATH)
        except Exception:
            pass
else:
    DB_DIR = Path(__file__).resolve().parent.parent / "data"
    DB_DIR.mkdir(exist_ok=True)
    DB_PATH = DB_DIR / "dj_microgreens.db"

class Row(tuple):
    """A result row readable by position (row[0]) or column name (row["name"]), like sqlite3.Row."""

    def __new__(cls, values, index):
        row = super().__new__(cls, values)
        row._index = index
        return row

    def __getitem__(self, key):
        if isinstance(key, str):
            return tuple.__getitem__(self, self._index[key])
        return tuple.__getitem__(self, key)

    def keys(self):
        return list(self._index)


class _Cursor:
    """Wraps a libsql cursor so rows behave like sqlite3.Row."""

    def __init__(self, cursor):
        self._cur = cursor

    def _index(self):
        return {d[0]: i for i, d in enumerate(self._cur.description or [])}

    def execute(self, sql, params=()):
        self._cur.execute(sql, tuple(params))
        return self

    def executemany(self, sql, seq):
        self._cur.executemany(sql, [tuple(p) for p in seq])
        return self

    def fetchone(self):
        row = self._cur.fetchone()
        return None if row is None else Row(row, self._index())

    def fetchall(self):
        index = self._index()
        return [Row(r, index) for r in self._cur.fetchall()]

    def __iter__(self):
        return iter(self.fetchall())

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    @property
    def rowcount(self):
        return self._cur.rowcount

    @property
    def description(self):
        return self._cur.description


class _Connection:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return _Cursor(self._conn.cursor())

    def execute(self, sql, params=()):
        return self.cursor().execute(sql, params)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()


_turso_lock = threading.RLock()
_turso_conn = None
_last_sync = 0.0
SYNC_EVERY_SECONDS = 1.0


def _get_turso_connection():
    """One shared connection per server instance, refreshed from Turso before use."""
    global _turso_conn, _last_sync
    import libsql

    if _turso_conn is None:
        raw = libsql.connect(
            str(DB_PATH), sync_url=TURSO_URL, auth_token=TURSO_TOKEN, _check_same_thread=False
        )
        _turso_conn = _Connection(raw)
        _last_sync = 0.0
    if time.time() - _last_sync > SYNC_EVERY_SECONDS:
        _turso_conn._conn.sync()
        _last_sync = time.time()
    return _turso_conn


def get_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=20.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def get_db():
    if USE_TURSO:
        with _turso_lock:
            conn = _get_turso_connection()
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return

    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Users
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Customers
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            email TEXT,
            password_hash TEXT,
            address TEXT,
            locality TEXT,
            pincode TEXT,
            customer_type TEXT DEFAULT 'Retail',
            total_orders INTEGER DEFAULT 0,
            lifetime_value REAL DEFAULT 0.0,
            last_order_date TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 3. Product Categories
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT,
            display_order INTEGER DEFAULT 0
        );
        """)

        # 4. Products
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT,
            taste_flavor TEXT,
            nutrition_info TEXT,
            health_benefits TEXT,
            grow_time_days INTEGER DEFAULT 10,
            image_url TEXT,
            is_active INTEGER DEFAULT 1,
            is_featured INTEGER DEFAULT 0,
            is_bestseller INTEGER DEFAULT 0,
            stock_quantity INTEGER DEFAULT 50,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES product_categories(id) ON DELETE SET NULL
        );
        """)

        # 5. Product Variants (Weight options: 50g, 100g, 250g, 500g)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            weight_label TEXT NOT NULL,
            weight_grams INTEGER NOT NULL,
            price REAL NOT NULL,
            b2b_price REAL NOT NULL,
            sku TEXT UNIQUE,
            is_available INTEGER DEFAULT 1,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        );
        """)

        # 6. Orders
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            customer_id INTEGER,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_email TEXT,
            order_date TEXT NOT NULL,
            delivery_date TEXT NOT NULL,
            delivery_slot TEXT DEFAULT 'Morning (7:00 AM - 9:00 AM)',
            subtotal REAL NOT NULL,
            delivery_fee REAL DEFAULT 0.0,
            discount REAL DEFAULT 0.0,
            gst REAL DEFAULT 0.0,
            total_amount REAL NOT NULL,
            payment_method TEXT DEFAULT 'UPI',
            payment_status TEXT DEFAULT 'Paid',
            payment_id TEXT,
            order_status TEXT DEFAULT 'Order Placed',
            shipping_address TEXT NOT NULL,
            shipping_locality TEXT,
            shipping_pincode TEXT NOT NULL,
            delivery_notes TEXT,
            assigned_delivery_person_id INTEGER,
            batch_id TEXT,
            tracking_timeline TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
            FOREIGN KEY (assigned_delivery_person_id) REFERENCES delivery_personnel(id) ON DELETE SET NULL
        );
        """)

        # GPS delivery location (added later; add the columns to older databases)
        order_cols = [r[1] for r in cursor.execute("PRAGMA table_info(orders)").fetchall()]
        for col in ("delivery_latitude", "delivery_longitude"):
            if col not in order_cols:
                cursor.execute(f"ALTER TABLE orders ADD COLUMN {col} REAL")

        # 7. Order Items
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER,
            variant_id INTEGER,
            product_name TEXT NOT NULL,
            weight_label TEXT NOT NULL,
            unit_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
            FOREIGN KEY (variant_id) REFERENCES product_variants(id) ON DELETE SET NULL
        );
        """)

        # 8. Payments
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            transaction_id TEXT UNIQUE NOT NULL,
            gateway TEXT DEFAULT 'Razorpay',
            method TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'INR',
            status TEXT DEFAULT 'Captured',
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            response_payload TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        );
        """)

        # 9. Subscriptions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            customer_name TEXT,
            customer_phone TEXT,
            plan_type TEXT NOT NULL,
            frequency TEXT NOT NULL,
            delivery_day TEXT NOT NULL,
            delivery_slot TEXT DEFAULT 'Morning (7:00 AM - 9:00 AM)',
            products_json TEXT NOT NULL,
            total_price_per_delivery REAL NOT NULL,
            status TEXT DEFAULT 'Active',
            start_date TEXT NOT NULL,
            next_delivery_date TEXT NOT NULL,
            paused_at TEXT,
            shipping_address TEXT,
            shipping_pincode TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
        );
        """)

        # 10. Delivery Personnel
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS delivery_personnel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            vehicle_number TEXT,
            assigned_zone TEXT,
            active_orders_count INTEGER DEFAULT 0,
            rating REAL DEFAULT 4.9,
            is_active INTEGER DEFAULT 1
        );
        """)

        # 11. Deliveries
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            delivery_person_id INTEGER,
            zone TEXT,
            pincode TEXT,
            scheduled_date TEXT,
            scheduled_slot TEXT,
            status TEXT DEFAULT 'Pending',
            actual_delivered_time TEXT,
            proof_notes TEXT,
            failure_reason TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (delivery_person_id) REFERENCES delivery_personnel(id) ON DELETE SET NULL
        );
        """)

        # 12. Cultivation Batches
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cultivation_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_code TEXT UNIQUE NOT NULL,
            product_id INTEGER,
            crop_variety TEXT NOT NULL,
            seed_quantity_grams REAL NOT NULL,
            tray_count INTEGER NOT NULL,
            tray_numbers TEXT,
            sowing_date TEXT NOT NULL,
            expected_germination_date TEXT NOT NULL,
            expected_harvest_date TEXT NOT NULL,
            actual_harvest_date TEXT,
            growing_stage TEXT DEFAULT 'Germinating',
            expected_yield_grams REAL NOT NULL,
            actual_yield_grams REAL DEFAULT 0.0,
            wastage_grams REAL DEFAULT 0.0,
            quality_grade TEXT DEFAULT 'Grade A+',
            inspection_notes TEXT,
            status TEXT DEFAULT 'Growing',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
        );
        """)

        # 13. Harvest Records
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS harvest_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL,
            batch_code TEXT NOT NULL,
            crop_variety TEXT NOT NULL,
            harvest_date TEXT NOT NULL,
            yield_grams REAL NOT NULL,
            operator_name TEXT NOT NULL,
            moisture_content TEXT DEFAULT 'Optimal (75-80%)',
            hygiene_pass INTEGER DEFAULT 1,
            packaged_units_50g INTEGER DEFAULT 0,
            packaged_units_100g INTEGER DEFAULT 0,
            packaged_units_250g INTEGER DEFAULT 0,
            packaged_units_500g INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Stored in Cold Room (4°C)',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (batch_id) REFERENCES cultivation_batches(id) ON DELETE CASCADE
        );
        """)

        # 14. Suppliers
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            contact_person TEXT,
            phone TEXT NOT NULL,
            email TEXT,
            address TEXT,
            gst_number TEXT,
            supplies_provided TEXT,
            rating REAL DEFAULT 4.8
        );
        """)

        # 15. Inventory
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_code TEXT UNIQUE NOT NULL,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit TEXT NOT NULL,
            opening_stock REAL NOT NULL,
            stock_received REAL DEFAULT 0.0,
            stock_consumed REAL DEFAULT 0.0,
            stock_available REAL NOT NULL,
            min_stock_threshold REAL NOT NULL,
            unit_cost REAL DEFAULT 0.0,
            supplier_id INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
        );
        """)

        # 16. Purchase Records
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT UNIQUE NOT NULL,
            supplier_id INTEGER,
            supplier_name TEXT,
            item_id INTEGER,
            item_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            total_amount REAL NOT NULL,
            purchase_date TEXT NOT NULL,
            payment_status TEXT DEFAULT 'Paid',
            invoice_number TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL,
            FOREIGN KEY (item_id) REFERENCES inventory(id) ON DELETE SET NULL
        );
        """)

        # 17. Coupons
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            discount_type TEXT NOT NULL,
            discount_value REAL NOT NULL,
            min_order_value REAL DEFAULT 0.0,
            max_discount REAL DEFAULT 500.0,
            valid_until TEXT,
            usage_limit INTEGER DEFAULT 1000,
            times_used INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        );
        """)

        # 18. Notifications
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_type TEXT NOT NULL,
            recipient_phone TEXT,
            recipient_email TEXT,
            notification_type TEXT NOT NULL,
            channel TEXT DEFAULT 'WhatsApp',
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'Delivered',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 19. Expenses
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_mode TEXT DEFAULT 'Bank Transfer',
            reference_voucher TEXT,
            approved_by TEXT DEFAULT 'Super Admin'
        );
        """)

        # 20. Audit Logs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT,
            change_summary TEXT,
            ip_address TEXT DEFAULT '127.0.0.1',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
