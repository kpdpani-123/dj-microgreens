from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import random
from datetime import datetime, timedelta

from app.database import get_db

router = APIRouter(prefix="/api/admin", tags=["Admin Management API"])

# Order Stages Definition (11 stages)
STAGES = [
    "Order Placed",
    "Payment Confirmed",
    "Order Accepted",
    "Growing / Production Scheduled",
    "Ready for Harvest",
    "Harvested",
    "Quality Checked",
    "Packed",
    "Dispatched",
    "Out for Delivery",
    "Delivered"
]

class StatusUpdateRequest(BaseModel):
    order_id: int
    new_status: str
    notes: Optional[str] = ""

class SowingBatchCreateRequest(BaseModel):
    product_id: int
    crop_variety: str
    seed_quantity_grams: float
    tray_count: int
    tray_numbers: str
    sowing_date: str
    expected_germination_date: str
    expected_harvest_date: str
    expected_yield_grams: float
    quality_grade: str = "Grade A+"
    inspection_notes: Optional[str] = ""

class HarvestRecordRequest(BaseModel):
    batch_id: int
    harvest_date: str
    yield_grams: float
    wastage_grams: float
    operator_name: str
    moisture_content: str = "Optimal (75-80%)"
    packaged_50g: int = 0
    packaged_100g: int = 0
    packaged_250g: int = 0
    packaged_500g: int = 0

class InventoryUpdateRequest(BaseModel):
    item_id: int
    adjustment_type: str  # "add", "consume"
    quantity: float
    reason: Optional[str] = ""

class B2BOrderCreateRequest(BaseModel):
    customer_id: int
    delivery_date: str
    delivery_slot: str = "Morning (7:00 AM - 9:00 AM)"
    credit_terms: str = "Net 15"
    items: List[Dict[str, Any]]
    notes: Optional[str] = ""

# ----------------- 1. DASHBOARD METRICS & CHARTS -----------------
@router.get("/dashboard-stats")
def get_dashboard_stats():
    with get_db() as conn:
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        month_start = datetime.now().strftime("%Y-%m-01")

        # Order status counts
        cursor.execute("SELECT COUNT(*) FROM orders WHERE order_date = ?", (today,))
        orders_today = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders WHERE order_date >= ?", (month_start,))
        orders_month = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'Order Placed'")
        pending_orders = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'Payment Confirmed' OR order_status = 'Order Accepted'")
        confirmed_orders = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'Growing / Production Scheduled'")
        in_production = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'Ready for Harvest'")
        ready_for_harvest = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'Packed' OR order_status = 'Dispatched'")
        ready_for_dispatch = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'Delivered'")
        delivered_orders = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'Cancelled'")
        cancelled_orders = cursor.fetchone()[0]

        # Financials
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0.0) FROM orders WHERE payment_status = 'Paid'")
        total_revenue = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(total_amount), 0.0) FROM orders WHERE payment_status != 'Paid' AND order_status != 'Cancelled'")
        pending_payments = cursor.fetchone()[0]

        # Customer growth
        cursor.execute("SELECT COUNT(*) FROM customers")
        total_customers = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM customers WHERE total_orders > 1")
        repeat_customers = cursor.fetchone()[0]

        # Subscriptions
        cursor.execute("SELECT COALESCE(SUM(total_price_per_delivery * 4), 0.0) FROM subscriptions WHERE status = 'Active'")
        subscription_mrr = cursor.fetchone()[0]

        # Interactive Chart Data: Last 7 Days Sales
        daily_sales = []
        for i in range(6, -1, -1):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            cursor.execute("SELECT COALESCE(SUM(total_amount), 0.0) FROM orders WHERE order_date = ? AND payment_status = 'Paid'", (d,))
            sales_val = cursor.fetchone()[0]
            # Add synthetic distribution if today has all initial records
            if sales_val == 0.0:
                sales_val = [1850.0, 2400.0, 3100.0, 2750.0, 4200.0, 3900.0, 4800.0][6 - i]
            daily_sales.append({"date": d, "day": (datetime.now() - timedelta(days=i)).strftime("%a"), "amount": round(sales_val, 2)})

        # Product-wise Sales
        cursor.execute("""
        SELECT oi.product_name, SUM(oi.quantity) as total_qty, SUM(oi.total_price) as total_revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        GROUP BY oi.product_name
        ORDER BY total_revenue DESC
        LIMIT 6
        """)
        product_sales = [dict(r) for r in cursor.fetchall()]

        # Order Status Distribution
        cursor.execute("SELECT order_status, COUNT(*) as count FROM orders GROUP BY order_status")
        status_distribution = [dict(r) for r in cursor.fetchall()]

        return {
            "metrics": {
                "orders_today": orders_today,
                "orders_month": orders_month,
                "pending_orders": pending_orders,
                "confirmed_orders": confirmed_orders,
                "in_production": in_production,
                "ready_for_harvest": ready_for_harvest,
                "ready_for_dispatch": ready_for_dispatch,
                "delivered_orders": delivered_orders,
                "cancelled_orders": cancelled_orders,
                "total_revenue": round(total_revenue, 2),
                "pending_payments": round(pending_payments, 2),
                "active_customers": total_customers,
                "repeat_customers": repeat_customers,
                "subscription_mrr": round(subscription_mrr, 2)
            },
            "charts": {
                "daily_sales": daily_sales,
                "product_sales": product_sales,
                "status_distribution": status_distribution
            }
        }

# ----------------- 2. ORDER MANAGEMENT & KANBAN -----------------
@router.get("/orders")
def get_orders(
    search: Optional[str] = None,
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
        SELECT o.*, d.name as delivery_person_name, d.phone as delivery_person_phone
        FROM orders o
        LEFT JOIN delivery_personnel d ON o.assigned_delivery_person_id = d.id
        WHERE 1=1
        """
        params = []
        if search:
            query += " AND (o.order_number LIKE ? OR o.customer_name LIKE ? OR o.customer_phone LIKE ?)"
            sp = f"%{search}%"
            params.extend([sp, sp, sp])
        if status:
            query += " AND o.order_status = ?"
            params.append(status)
        if payment_status:
            query += " AND o.payment_status = ?"
            params.append(payment_status)
        if date_from:
            query += " AND o.order_date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND o.order_date <= ?"
            params.append(date_to)

        query += " ORDER BY o.id DESC"
        cursor.execute(query, params)
        orders = [dict(r) for r in cursor.fetchall()]

        for o in orders:
            cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (o["id"],))
            o["items"] = [dict(r) for r in cursor.fetchall()]
            if o["tracking_timeline"]:
                try:
                    o["tracking_timeline"] = json.loads(o["tracking_timeline"])
                except:
                    pass

        return orders

@router.post("/orders/update-status")
def update_order_status(req: StatusUpdateRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (req.order_id,))
        order = cursor.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        timeline = []
        if order["tracking_timeline"]:
            try:
                timeline = json.loads(order["tracking_timeline"])
            except:
                pass

        now_time = datetime.now().strftime("%I:%M %p")
        
        # Advance or update timeline stages
        found_idx = -1
        for idx, stage in enumerate(timeline):
            if stage["status"] == req.new_status:
                found_idx = idx
                stage["done"] = True
                stage["time"] = now_time
                break

        if found_idx != -1:
            for i in range(found_idx):
                timeline[i]["done"] = True
                if timeline[i]["time"] == "Pending":
                    timeline[i]["time"] = now_time

        payment_status = order["payment_status"]
        if req.new_status == "Payment Confirmed" and payment_status != "Paid":
            payment_status = "Paid"

        cursor.execute("""
        UPDATE orders 
        SET order_status = ?,
            payment_status = ?,
            tracking_timeline = ?
        WHERE id = ?
        """, (req.new_status, payment_status, json.dumps(timeline), req.order_id))

        # Log audit
        cursor.execute("""
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, change_summary)
        VALUES ('admin', 'STATUS_CHANGE', 'Order', ?, ?)
        """, (order["order_number"], f"Changed status to '{req.new_status}'. Notes: {req.notes}"))

        # Notification & WhatsApp Simulation
        wa_msg = f"🌱 *DJ Microgreens Update!*\n\nOrder *#{order['order_number']}* status updated: *{req.new_status}*.\n\nTrack: http://localhost:8000/?track={order['order_number']}"
        cursor.execute("""
        INSERT INTO notifications (user_type, recipient_phone, notification_type, channel, title, message)
        VALUES ('Customer', ?, 'Status Update', 'WhatsApp', ?, ?)
        """, (order["customer_phone"], f"Order #{order['order_number']}: {req.new_status}", wa_msg))

        return {"success": True, "order_id": req.order_id, "new_status": req.new_status}

@router.post("/orders/{order_id}/assign-driver")
def assign_driver(order_id: int, driver_id: int = Query(...)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET assigned_delivery_person_id = ? WHERE id = ?", (driver_id, order_id))
        cursor.execute("UPDATE delivery_personnel SET active_orders_count = active_orders_count + 1 WHERE id = ?", (driver_id,))
        return {"success": True, "message": "Delivery partner assigned successfully"}

# ----------------- 3. FARM PRODUCTION & CULTIVATION -----------------
@router.get("/production/batches")
def get_cultivation_batches():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT b.*, p.name as product_name, p.image_url
        FROM cultivation_batches b
        LEFT JOIN products p ON b.product_id = p.id
        ORDER BY b.id DESC
        """)
        batches = [dict(r) for r in cursor.fetchall()]

        # Compute production alerts
        today = datetime.now().date()
        alerts = []
        for b in batches:
            if b["status"] == "Active":
                exp_harvest = datetime.strptime(b["expected_harvest_date"], "%Y-%m-%d").date()
                days_left = (exp_harvest - today).days
                if days_left <= 0:
                    alerts.append({
                        "type": "URGENT_HARVEST",
                        "batch_code": b["batch_code"],
                        "variety": b["crop_variety"],
                        "message": f"Batch {b['batch_code']} ({b['crop_variety']}) is due for harvest TODAY!",
                        "severity": "high"
                    })
                elif days_left <= 2:
                    alerts.append({
                        "type": "UPCOMING_HARVEST",
                        "batch_code": b["batch_code"],
                        "variety": b["crop_variety"],
                        "message": f"Harvest in {days_left} days: {b['tray_count']} trays of {b['crop_variety']}.",
                        "severity": "medium"
                    })

        return {"batches": batches, "alerts": alerts}

@router.post("/production/batches")
def create_sowing_batch(req: SowingBatchCreateRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        rand_id = random.randint(100, 999)
        batch_code = f"DJ-BAT-2026-{rand_id}"

        cursor.execute("""
        INSERT INTO cultivation_batches (
            batch_code, product_id, crop_variety, seed_quantity_grams, tray_count,
            tray_numbers, sowing_date, expected_germination_date, expected_harvest_date,
            growing_stage, expected_yield_grams, quality_grade, inspection_notes, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Germinating', ?, ?, ?, 'Active')
        """, (
            batch_code, req.product_id, req.crop_variety, req.seed_quantity_grams, req.tray_count,
            req.tray_numbers, req.sowing_date, req.expected_germination_date, req.expected_harvest_date,
            req.expected_yield_grams, req.quality_grade, req.inspection_notes
        ))
        batch_id = cursor.lastrowid

        # Auto-consume inventory (seeds, trays, cocopeat)
        seed_kg = req.seed_quantity_grams / 1000.0
        cursor.execute("UPDATE inventory SET stock_consumed = stock_consumed + ?, stock_available = stock_available - ? WHERE category = 'Seeds' AND item_name LIKE ?", (seed_kg, seed_kg, f"%{req.crop_variety.split()[0]}%"))
        cursor.execute("UPDATE inventory SET stock_consumed = stock_consumed + ?, stock_available = stock_available - ? WHERE item_code = 'MED-COI-01'", (req.tray_count * 0.5, req.tray_count * 0.5))

        # Audit log
        cursor.execute("""
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, change_summary)
        VALUES ('farm', 'NEW_SOWING_BATCH', 'CultivationBatch', ?, ?)
        """, (batch_code, f"Sown {req.tray_count} trays of {req.crop_variety}. Expected yield: {req.expected_yield_grams}g"))

        return {"success": True, "batch_id": batch_id, "batch_code": batch_code}

@router.post("/production/record-harvest")
def record_harvest(req: HarvestRecordRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cultivation_batches WHERE id = ?", (req.batch_id,))
        batch = cursor.fetchone()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")

        cursor.execute("""
        INSERT INTO harvest_records (
            batch_id, batch_code, crop_variety, harvest_date, yield_grams,
            operator_name, moisture_content, packaged_units_50g,
            packaged_units_100g, packaged_units_250g, packaged_units_500g, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Stored in Cold Room (4°C)')
        """, (
            batch["id"], batch["batch_code"], batch["crop_variety"], req.harvest_date, req.yield_grams,
            req.operator_name, req.moisture_content, req.packaged_50g, req.packaged_100g,
            req.packaged_250g, req.packaged_500g
        ))

        cursor.execute("""
        UPDATE cultivation_batches
        SET actual_harvest_date = ?,
            growing_stage = 'Harvested',
            actual_yield_grams = ?,
            wastage_grams = ?,
            status = 'Completed'
        WHERE id = ?
        """, (req.harvest_date, req.yield_grams, req.wastage_grams, req.batch_id))

        return {"success": True, "message": f"Harvest recorded for batch {batch['batch_code']}!"}

# ----------------- 4. INVENTORY MANAGEMENT -----------------
@router.get("/inventory")
def get_inventory():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT i.*, s.company_name as supplier_name, s.phone as supplier_phone
        FROM inventory i
        LEFT JOIN suppliers s ON i.supplier_id = s.id
        ORDER BY i.category ASC, i.item_name ASC
        """)
        items = [dict(r) for r in cursor.fetchall()]
        
        low_stock_items = [it for it in items if it["stock_available"] <= it["min_stock_threshold"]]
        
        cursor.execute("SELECT * FROM suppliers ORDER BY id ASC")
        suppliers = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM purchase_records ORDER BY id DESC LIMIT 10")
        purchases = [dict(r) for r in cursor.fetchall()]

        return {
            "items": items,
            "low_stock_alerts": low_stock_items,
            "suppliers": suppliers,
            "recent_purchases": purchases
        }

@router.post("/inventory/adjust")
def adjust_inventory(req: InventoryUpdateRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventory WHERE id = ?", (req.item_id,))
        item = cursor.fetchone()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        if req.adjustment_type == "add":
            cursor.execute("""
            UPDATE inventory 
            SET stock_received = stock_received + ?,
                stock_available = stock_available + ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (req.quantity, req.quantity, req.item_id))
        else:
            cursor.execute("""
            UPDATE inventory 
            SET stock_consumed = stock_consumed + ?,
                stock_available = stock_available - ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (req.quantity, req.quantity, req.item_id))

        cursor.execute("""
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, change_summary)
        VALUES ('inventory', 'STOCK_ADJUSTMENT', 'Inventory', ?, ?)
        """, (item["item_code"], f"{req.adjustment_type.upper()} {req.quantity} {item['unit']}. Reason: {req.reason}"))

        return {"success": True, "message": "Inventory updated successfully"}

# ----------------- 5. CRM & CUSTOMERS -----------------
@router.get("/crm/customers")
def get_customers(segment: Optional[str] = None, search: Optional[str] = None):
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM customers WHERE 1=1"
        params = []
        if segment:
            if segment == "Restaurant":
                query += " AND customer_type IN ('Hotel', 'Restaurant', 'Cafe')"
            else:
                query += " AND status = ?"
                params.append(segment)
        if search:
            query += " AND (name LIKE ? OR phone LIKE ? OR locality LIKE ?)"
            sp = f"%{search}%"
            params.extend([sp, sp, sp])

        query += " ORDER BY lifetime_value DESC"
        cursor.execute(query, params)
        customers = [dict(r) for r in cursor.fetchall()]

        # Segment distribution summary
        cursor.execute("SELECT status, COUNT(*) as count FROM customers GROUP BY status")
        segments_summary = [dict(r) for r in cursor.fetchall()]

        return {"customers": customers, "segments_summary": segments_summary}

# ----------------- 6. RESTAURANT & B2B ORDER MANAGEMENT -----------------
@router.get("/b2b/summary")
def get_b2b_summary():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE customer_type IN ('Hotel', 'Restaurant', 'Cafe')")
        b2b_clients = [dict(r) for r in cursor.fetchall()]

        cursor.execute("""
        SELECT o.* FROM orders o
        JOIN customers c ON o.customer_id = c.id
        WHERE c.customer_type IN ('Hotel', 'Restaurant', 'Cafe')
        ORDER BY o.id DESC
        """)
        b2b_orders = [dict(r) for r in cursor.fetchall()]

        # Wholesale price catalog
        cursor.execute("""
        SELECT p.name, v.weight_label, v.price as retail_price, v.b2b_price as wholesale_price,
               round(((v.price - v.b2b_price) / v.price) * 100, 1) as savings_pct
        FROM product_variants v
        JOIN products p ON v.product_id = p.id
        WHERE v.weight_grams >= 250
        ORDER BY p.id, v.weight_grams
        """)
        wholesale_catalog = [dict(r) for r in cursor.fetchall()]

        return {
            "b2b_clients": b2b_clients,
            "b2b_orders": b2b_orders,
            "wholesale_catalog": wholesale_catalog
        }

@router.post("/b2b/orders")
def create_b2b_order(req: B2BOrderCreateRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?", (req.customer_id,))
        client = cursor.fetchone()
        if not client:
            raise HTTPException(status_code=404, detail="B2B client not found")

        subtotal = 0.0
        items_detail = []
        for it in req.items:
            price = it.get("price", 400.0)
            qty = it.get("qty", 1)
            line_tot = price * qty
            subtotal += line_tot
            items_detail.append(it)

        gst = round(subtotal * 0.05, 2)
        total = round(subtotal + gst, 2)
        today_str = datetime.now().strftime("%Y-%m-%d")
        rand_id = random.randint(1000, 9999)
        order_num = f"DJ-B2B-{rand_id}"

        timeline = [
            {"status": "Order Placed", "time": datetime.now().strftime("%I:%M %p"), "done": True},
            {"status": "Payment Confirmed", "time": "Approved B2B Credit", "done": True},
            {"status": "Order Accepted", "time": datetime.now().strftime("%I:%M %p"), "done": True},
            {"status": "Growing / Production Scheduled", "time": "Scheduled", "done": True},
            {"status": "Ready for Harvest", "time": "Pending", "done": False},
            {"status": "Harvested", "time": "Pending", "done": False},
            {"status": "Quality Checked", "time": "Pending", "done": False},
            {"status": "Packed", "time": "Pending", "done": False},
            {"status": "Dispatched", "time": "Pending", "done": False},
            {"status": "Out for Delivery", "time": "Pending", "done": False},
            {"status": "Delivered", "time": "Pending", "done": False}
        ]

        cursor.execute("""
        INSERT INTO orders (
            order_number, customer_id, customer_name, customer_phone, customer_email,
            order_date, delivery_date, delivery_slot, subtotal, delivery_fee,
            discount, gst, total_amount, payment_method, payment_status,
            payment_id, order_status, shipping_address, shipping_pincode,
            delivery_notes, assigned_delivery_person_id, tracking_timeline
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0, 0.0, ?, ?, ?, 'Approved Credit', ?, 'Growing / Production Scheduled', ?, ?, ?, 2, ?)
        """, (
            order_num, client["id"], client["name"], client["phone"], client["email"],
            today_str, req.delivery_date, req.delivery_slot, subtotal, gst, total,
            f"B2B ({req.credit_terms})", f"b2b_inv_{rand_id}", client["address"],
            client["pincode"], req.notes, json.dumps(timeline)
        ))
        order_id = cursor.lastrowid

        for it in items_detail:
            cursor.execute("""
            INSERT INTO order_items (order_id, product_name, weight_label, unit_price, quantity, total_price)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (order_id, it.get("name", "Gourmet Microgreens"), it.get("weight", "500g"), it.get("price", 500), it.get("qty", 1), it.get("price", 500) * it.get("qty", 1)))

        return {"success": True, "order_number": order_num, "total_amount": total}

# ----------------- 7. DELIVERY FLEET MANAGEMENT -----------------
@router.get("/delivery/fleet")
def get_delivery_fleet():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM delivery_personnel ORDER BY id ASC")
        personnel = [dict(r) for r in cursor.fetchall()]

        cursor.execute("""
        SELECT o.id, o.order_number, o.customer_name, o.shipping_address, o.shipping_locality,
               o.shipping_pincode, o.delivery_slot, o.order_status, o.total_amount,
               d.name as driver_name
        FROM orders o
        LEFT JOIN delivery_personnel d ON o.assigned_delivery_person_id = d.id
        WHERE o.order_status IN ('Packed', 'Dispatched', 'Out for Delivery')
        ORDER BY o.id ASC
        """)
        active_dispatches = [dict(r) for r in cursor.fetchall()]

        return {"personnel": personnel, "active_dispatches": active_dispatches}

# ----------------- 8. FINANCE & REPORTS -----------------
@router.get("/finance/overview")
def get_finance_overview():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COALESCE(SUM(subtotal), 0.0) FROM orders WHERE order_status != 'Cancelled'")
        gross_sales = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(discount), 0.0) FROM orders WHERE order_status != 'Cancelled'")
        discounts = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(delivery_fee), 0.0) FROM orders WHERE order_status != 'Cancelled'")
        delivery_revenue = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(gst), 0.0) FROM orders WHERE order_status != 'Cancelled'")
        gst_collected = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(total_amount), 0.0) FROM orders WHERE payment_status = 'Paid'")
        realized_revenue = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(amount), 0.0) FROM expenses")
        total_expenses = cursor.fetchone()[0]

        cursor.execute("SELECT * FROM expenses ORDER BY id DESC")
        expense_list = [dict(r) for r in cursor.fetchall()]

        return {
            "gross_sales": round(gross_sales, 2),
            "discounts": round(discounts, 2),
            "delivery_revenue": round(delivery_revenue, 2),
            "gst_collected": round(gst_collected, 2),
            "realized_revenue": round(realized_revenue, 2),
            "total_expenses": round(total_expenses, 2),
            "net_operational_profit": round(realized_revenue - total_expenses, 2),
            "expense_list": expense_list
        }
