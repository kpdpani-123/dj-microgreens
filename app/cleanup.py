"""One-time removal of the demo data the app was first seeded with.

Runs once per database (tracked in app_settings). Only removes records that
still match the original demo values, so anything staff entered is kept.
"""
from app.database import get_db

FLAG = "demo_cleanup_v2"

DEMO_BATCH_CODES = [f"DJ-BAT-2026-{n:03d}" for n in range(81, 87)]  # DJ-BAT-2026-081 ... 086

# item_code -> (opening_stock, min_stock_threshold) as originally seeded
DEMO_INVENTORY = {
    "RAW-SED-01": (15.0, 5.0),
    "RAW-SED-02": (40.0, 15.0),
    "RAW-SED-03": (20.0, 8.0),
    "RAW-SED-04": (50.0, 20.0),
    "MED-COI-01": (120.0, 30.0),
    "HAR-TRY-01": (400.0, 50.0),
    "PKG-BOX-01": (2500.0, 500.0),
    "PKG-BOX-02": (3000.0, 600.0),
    "PKG-SEAL-01": (50.0, 10.0),
}

DEMO_PURCHASE_ORDERS = ["PO-2026-041", "PO-2026-042", "PO-2026-043"]
DEMO_SUPPLIERS = ["GreenSeeds India Organics", "Tamil Nadu Coir Board Bio-Medium", "EcoPack Bio Solutions"]
DEMO_CHEF_PHONES = ["+91 99620 44321", "+91 98410 77654", "+91 98400 99887"]


def remove_demo_data():
    with get_db() as conn:
        done = conn.execute("SELECT value FROM app_settings WHERE key = ?", (FLAG,)).fetchone()
        if done:
            return

        # Cultivation batches and their harvest records
        marks = ",".join("?" * len(DEMO_BATCH_CODES))
        conn.execute(f"DELETE FROM harvest_records WHERE batch_code IN ({marks})", DEMO_BATCH_CODES)
        conn.execute(f"DELETE FROM cultivation_batches WHERE batch_code IN ({marks})", DEMO_BATCH_CODES)

        # Inventory: keep the item list, clear the demo numbers and suppliers
        for code, (opening, minimum) in DEMO_INVENTORY.items():
            conn.execute(
                """UPDATE inventory
                   SET opening_stock = 0, stock_received = 0, stock_consumed = 0, stock_available = 0,
                       min_stock_threshold = 0, unit_cost = 0, supplier_id = NULL, supplier_name = NULL
                   WHERE item_code = ? AND opening_stock = ? AND min_stock_threshold = ?""",
                (code, opening, minimum),
            )

        marks = ",".join("?" * len(DEMO_PURCHASE_ORDERS))
        conn.execute(f"DELETE FROM purchase_records WHERE po_number IN ({marks})", DEMO_PURCHASE_ORDERS)
        marks = ",".join("?" * len(DEMO_SUPPLIERS))
        conn.execute(f"UPDATE inventory SET supplier_id = NULL WHERE supplier_id IN (SELECT id FROM suppliers WHERE company_name IN ({marks}))", DEMO_SUPPLIERS)
        conn.execute(f"DELETE FROM suppliers WHERE company_name IN ({marks})", DEMO_SUPPLIERS)

        # Demo chef accounts that never ordered
        marks = ",".join("?" * len(DEMO_CHEF_PHONES))
        conn.execute(
            f"""DELETE FROM customers WHERE phone IN ({marks}) AND COALESCE(total_orders, 0) = 0
                AND id NOT IN (SELECT customer_id FROM orders WHERE customer_id IS NOT NULL)""",
            DEMO_CHEF_PHONES,
        )

        conn.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, 'done')", (FLAG,))
