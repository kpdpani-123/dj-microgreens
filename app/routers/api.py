from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
from datetime import datetime, timedelta
import random

from app.database import get_db
from app.customer_auth import current_customer, sign_in_enabled, find_customer_by_phone, normalize_phone, site_url, phone_digits

router = APIRouter(prefix="/api", tags=["Customer API"])

# Chennai Pincode Matrix: 600001 to 600130
CHENNAI_AREAS = {
    "600001": {"area": "George Town / Parrys", "zone": "North Chennai", "available": True, "lead_time_hrs": 3},
    "600002": {"area": "Mount Road / Anna Salai", "zone": "Central Chennai", "available": True, "lead_time_hrs": 2},
    "600004": {"area": "Mylapore", "zone": "South Chennai", "available": True, "lead_time_hrs": 2},
    "600006": {"area": "Nungambakkam", "zone": "Central Chennai", "available": True, "lead_time_hrs": 2},
    "600017": {"area": "T. Nagar", "zone": "Central Chennai", "available": True, "lead_time_hrs": 2},
    "600018": {"area": "Alwarpet / Teynampet", "zone": "Central Chennai", "available": True, "lead_time_hrs": 2},
    "600020": {"area": "Adyar / Gandhi Nagar", "zone": "South Chennai", "available": True, "lead_time_hrs": 2},
    "600028": {"area": "R.A. Puram", "zone": "South Chennai", "available": True, "lead_time_hrs": 2},
    "600032": {"area": "Guindy / Ekkatuthangal", "zone": "Central South (Near Farm)", "available": True, "lead_time_hrs": 1.5},
    "600040": {"area": "Anna Nagar", "zone": "West Chennai", "available": True, "lead_time_hrs": 2.5},
    "600041": {"area": "Thiruvanmiyur / Valmiki Nagar", "zone": "South Coastal", "available": True, "lead_time_hrs": 2},
    "600042": {"area": "Velachery", "zone": "South Chennai", "available": True, "lead_time_hrs": 2},
    "600096": {"area": "Perungudi / OMR Phase 1", "zone": "OMR Tech Corridor", "available": True, "lead_time_hrs": 2.5},
    "600097": {"area": "Thoraipakkam / OMR", "zone": "OMR Tech Corridor", "available": True, "lead_time_hrs": 2.5},
    "600100": {"area": "Medavakkam / Pallikaranai", "zone": "South Chennai", "available": True, "lead_time_hrs": 3},
    "600119": {"area": "Sholinganallur / OMR", "zone": "OMR Tech Corridor", "available": True, "lead_time_hrs": 3},
    "600130": {"area": "Navalur / Siruseri SIPCOT", "zone": "OMR IT Corridor", "available": True, "lead_time_hrs": 3.5}
}

class PincodeCheckRequest(BaseModel):
    pincode: str

class CartItem(BaseModel):
    product_id: int
    variant_id: int
    weight_label: str
    quantity: int

class CartCalculateRequest(BaseModel):
    items: List[CartItem]
    coupon_code: Optional[str] = None
    pincode: Optional[str] = None

class OrderCreateRequest(BaseModel):
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    shipping_address: str
    shipping_locality: Optional[str] = ""
    shipping_pincode: str
    delivery_date: str
    delivery_slot: str
    delivery_notes: Optional[str] = ""
    payment_method: str = "UPI"
    coupon_code: Optional[str] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    items: List[CartItem]

class SubscriptionCreateRequest(BaseModel):
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    shipping_address: str
    shipping_pincode: str
    plan_type: str
    frequency: str
    delivery_day: str
    delivery_slot: str = "Morning (7:00 AM - 9:00 AM)"
    products: List[Dict[str, Any]]

class UserLoginRequest(BaseModel):
    username: str
    password: str

# ----------------- PINCODE CHECKER -----------------
@router.post("/check-pincode")
def check_pincode(req: PincodeCheckRequest):
    code = req.pincode.strip()
    if not (code.startswith("600") and len(code) == 6 and code.isdigit()):
        return {
            "available": False,
            "message": "DJ Microgreens currently delivers exclusively across Chennai urban & suburban pincodes (600001 - 600130).",
            "pincode": code
        }
    
    info = CHENNAI_AREAS.get(code)
    if info:
        return {
            "available": True,
            "area": info["area"],
            "zone": info["zone"],
            "lead_time_hrs": info["lead_time_hrs"],
            "free_delivery_above": 499,
            "delivery_fee": 50,
            "next_slot": "Tomorrow Morning 7:00 AM - 9:00 AM",
            "message": f"Fresh farm harvest delivery is available in {info['area']} ({info['zone']})!"
        }
    else:
        # Default Chennai pincode coverage
        return {
            "available": True,
            "area": "Greater Chennai Metropolitan Area",
            "zone": "Chennai Extended Zone",
            "lead_time_hrs": 4,
            "free_delivery_above": 499,
            "delivery_fee": 50,
            "next_slot": "Tomorrow Morning 7:00 AM - 9:00 AM",
            "message": "Delivery available! Freshly harvested and delivered via temperature-controlled EV logistics."
        }

# ----------------- PRODUCTS & CATEGORIES -----------------
@router.get("/categories")
def get_categories():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product_categories ORDER BY display_order ASC")
        return [dict(row) for row in cursor.fetchall()]

@router.get("/products")
def get_products(category_id: Optional[int] = None, search: Optional[str] = None, featured_only: bool = False):
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
        SELECT p.*, c.name as category_name 
        FROM products p
        LEFT JOIN product_categories c ON p.category_id = c.id
        WHERE p.is_active = 1
        """
        params = []
        if category_id:
            query += " AND p.category_id = ?"
            params.append(category_id)
        if search:
            query += " AND (p.name LIKE ? OR p.description LIKE ? OR p.taste_flavor LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        if featured_only:
            query += " AND p.is_featured = 1"

        query += " ORDER BY p.id ASC"
        cursor.execute(query, params)
        products = [dict(row) for row in cursor.fetchall()]

        # Fetch variants for each product
        for prod in products:
            cursor.execute("""
            SELECT * FROM product_variants 
            WHERE product_id = ? AND is_available = 1
            ORDER BY weight_grams ASC
            """, (prod["id"],))
            prod["variants"] = [dict(v) for v in cursor.fetchall()]

        return products

@router.get("/products/{product_id}")
def get_product_detail(product_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT p.*, c.name as category_name 
        FROM products p
        LEFT JOIN product_categories c ON p.category_id = c.id
        WHERE p.id = ?
        """, (product_id,))
        prod = cursor.fetchone()
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")
        
        prod_dict = dict(prod)
        cursor.execute("""
        SELECT * FROM product_variants 
        WHERE product_id = ? AND is_available = 1
        ORDER BY weight_grams ASC
        """, (product_id,))
        prod_dict["variants"] = [dict(v) for v in cursor.fetchall()]
        return prod_dict

# ----------------- CART & COUPON ENGINE -----------------
@router.post("/cart/calculate")
def calculate_cart(req: CartCalculateRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        subtotal = 0.0
        calculated_items = []

        for item in req.items:
            cursor.execute("""
            SELECT v.id as variant_id, v.weight_label, v.price, p.id as product_id, p.name, p.image_url
            FROM product_variants v
            JOIN products p ON v.product_id = p.id
            WHERE v.id = ? AND p.id = ?
            """, (item.variant_id, item.product_id))
            row = cursor.fetchone()
            if row:
                line_total = row["price"] * item.quantity
                subtotal += line_total
                calculated_items.append({
                    "product_id": row["product_id"],
                    "variant_id": row["variant_id"],
                    "name": row["name"],
                    "weight_label": row["weight_label"],
                    "unit_price": row["price"],
                    "quantity": item.quantity,
                    "line_total": line_total,
                    "image_url": row["image_url"]
                })

        # Delivery fee: Free for orders >= 499, else 50
        delivery_fee = 0.0 if subtotal >= 499.0 or subtotal == 0 else 50.0

        # Coupon calculation
        discount = 0.0
        coupon_applied = None
        coupon_error = None

        if req.coupon_code:
            code_clean = req.coupon_code.strip().upper()
            cursor.execute("SELECT * FROM coupons WHERE code = ? AND is_active = 1", (code_clean,))
            coupon = cursor.fetchone()
            if coupon:
                if subtotal < coupon["min_order_value"]:
                    coupon_error = f"Minimum order value for coupon {code_clean} is ₹{coupon['min_order_value']:.0f}"
                else:
                    if coupon["discount_type"] == "Percentage":
                        raw_disc = (subtotal * coupon["discount_value"]) / 100.0
                        discount = min(raw_disc, coupon["max_discount"])
                    else:
                        discount = min(coupon["discount_value"], subtotal)
                    coupon_applied = {
                        "code": code_clean,
                        "discount_type": coupon["discount_type"],
                        "discount_value": coupon["discount_value"],
                        "discount_amount": round(discount, 2)
                    }
            else:
                coupon_error = "Invalid or expired coupon code"

        # GST 5% on subtotal after discount
        taxable_amount = max(0.0, subtotal - discount)
        gst = round(taxable_amount * 0.05, 2)
        total_amount = round(taxable_amount + gst + delivery_fee, 2)

        return {
            "items": calculated_items,
            "subtotal": round(subtotal, 2),
            "discount": round(discount, 2),
            "coupon_applied": coupon_applied,
            "coupon_error": coupon_error,
            "delivery_fee": delivery_fee,
            "gst": gst,
            "total_amount": total_amount,
            "free_delivery_threshold": 499.0,
            "amount_needed_for_free_delivery": max(0.0, round(499.0 - subtotal, 2))
        }

# ----------------- CHECKOUT & ORDERS -----------------
@router.post("/orders")
def create_order(req: OrderCreateRequest, request: Request):
    if not req.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    with get_db() as conn:
        cursor = conn.cursor()
        signed_in = current_customer(request, conn)
        if sign_in_enabled() and not signed_in:
            raise HTTPException(status_code=401, detail="Please log in to place your order")
        if signed_in:
            # The signed-in account decides who the order belongs to
            if not phone_digits(signed_in.get("phone") or ""):
                raise HTTPException(status_code=400, detail="Please add your mobile number to your account first")
            req.customer_phone = signed_in["phone"]
        
        # 1. Calculate pricing
        subtotal = 0.0
        order_items_data = []

        for item in req.items:
            cursor.execute("""
            SELECT v.id as variant_id, v.weight_label, v.price, p.id as product_id, p.name
            FROM product_variants v
            JOIN products p ON v.product_id = p.id
            WHERE v.id = ? AND p.id = ?
            """, (item.variant_id, item.product_id))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=400, detail=f"Invalid variant ID {item.variant_id}")
            
            line_total = row["price"] * item.quantity
            subtotal += line_total
            order_items_data.append({
                "product_id": row["product_id"],
                "variant_id": row["variant_id"],
                "name": row["name"],
                "weight_label": row["weight_label"],
                "unit_price": row["price"],
                "quantity": item.quantity,
                "total_price": line_total
            })

        # Apply coupon if given
        discount = 0.0
        if req.coupon_code:
            code_clean = req.coupon_code.strip().upper()
            cursor.execute("SELECT * FROM coupons WHERE code = ? AND is_active = 1", (code_clean,))
            coupon = cursor.fetchone()
            if coupon and subtotal >= coupon["min_order_value"]:
                if coupon["discount_type"] == "Percentage":
                    discount = min((subtotal * coupon["discount_value"]) / 100.0, coupon["max_discount"])
                else:
                    discount = min(coupon["discount_value"], subtotal)
                cursor.execute("UPDATE coupons SET times_used = times_used + 1 WHERE id = ?", (coupon["id"],))

        delivery_fee = 0.0 if subtotal >= 499.0 else 50.0
        taxable_amount = max(0.0, subtotal - discount)
        gst = round(taxable_amount * 0.05, 2)
        total_amount = round(taxable_amount + gst + delivery_fee, 2)

        # 2. Get or create customer
        today_str = datetime.now().strftime("%Y-%m-%d")
        if signed_in:
            cust = signed_in
        else:
            cust = find_customer_by_phone(conn, req.customer_phone) if normalize_phone(req.customer_phone) else None
            if not cust:
                cursor.execute("SELECT id, total_orders, lifetime_value FROM customers WHERE phone = ?", (req.customer_phone.strip(),))
                cust = cursor.fetchone()

        if signed_in:
            customer_id = cust["id"]
            cursor.execute("""
            UPDATE customers
            SET total_orders = total_orders + 1,
                lifetime_value = lifetime_value + ?,
                last_order_date = ?,
                name = CASE WHEN COALESCE(name, '') = '' THEN ? ELSE name END,
                email = CASE WHEN COALESCE(email, '') = '' THEN ? ELSE email END,
                address = CASE WHEN COALESCE(address, '') = '' THEN ? ELSE address END,
                locality = CASE WHEN COALESCE(locality, '') = '' THEN ? ELSE locality END,
                pincode = CASE WHEN COALESCE(pincode, '') = '' THEN ? ELSE pincode END
            WHERE id = ?
            """, (total_amount, today_str, req.customer_name, req.customer_email or "", req.shipping_address,
                  req.shipping_locality or "", req.shipping_pincode, customer_id))
        elif cust:
            customer_id = cust["id"]
            cursor.execute("""
            UPDATE customers 
            SET total_orders = total_orders + 1,
                lifetime_value = lifetime_value + ?,
                last_order_date = ?,
                address = ?,
                pincode = ?
            WHERE id = ?
            """, (total_amount, today_str, req.shipping_address, req.shipping_pincode, customer_id))
        else:
            cursor.execute("""
            INSERT INTO customers (name, phone, email, address, locality, pincode, total_orders, lifetime_value, last_order_date)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (req.customer_name, normalize_phone(req.customer_phone) or req.customer_phone.strip(), req.customer_email, req.shipping_address, req.shipping_locality, req.shipping_pincode, total_amount, today_str))
            customer_id = cursor.lastrowid

        # GPS delivery spot (only keep sensible coordinates)
        lat, lng = req.delivery_latitude, req.delivery_longitude
        if lat is None or lng is None or not (-90 <= lat <= 90 and -180 <= lng <= 180):
            lat = lng = None
        map_line = f"\n🗺️ Location: https://www.google.com/maps?q={lat},{lng}" if lat is not None else ""

        # 3. Generate Unique Order Number
        rand_num = random.randint(1000, 9999)
        order_number = f"DJ-{datetime.now().year}-{rand_num}"

        # Assign delivery partner based on zone/pincode
        cursor.execute("SELECT id FROM delivery_personnel WHERE is_active = 1 ORDER BY active_orders_count ASC LIMIT 1")
        del_person = cursor.fetchone()
        del_person_id = del_person["id"] if del_person else 1

        # Link to active batch
        cursor.execute("SELECT batch_code FROM cultivation_batches WHERE status = 'Active' ORDER BY id ASC LIMIT 1")
        batch = cursor.fetchone()
        batch_id = batch["batch_code"] if batch else None

        # 11 Stages Timeline Initialization
        now_time = datetime.now().strftime("%I:%M %p")
        timeline = [
            {"status": "Order Placed", "time": now_time, "done": True},
            {"status": "Payment Confirmed", "time": now_time if req.payment_method != "Cash on Delivery" else "Pending", "done": req.payment_method != "Cash on Delivery"},
            {"status": "Order Accepted", "time": "Pending", "done": False},
            {"status": "Growing / Production Scheduled", "time": "Pending", "done": False},
            {"status": "Ready for Harvest", "time": "Pending", "done": False},
            {"status": "Harvested", "time": "Pending", "done": False},
            {"status": "Quality Checked", "time": "Pending", "done": False},
            {"status": "Packed", "time": "Pending", "done": False},
            {"status": "Dispatched", "time": "Pending", "done": False},
            {"status": "Out for Delivery", "time": "Pending", "done": False},
            {"status": "Delivered", "time": "Pending", "done": False}
        ]

        order_status = "Payment Confirmed" if req.payment_method != "Cash on Delivery" else "Order Placed"
        payment_status = "Paid" if req.payment_method != "Cash on Delivery" else "Pending"
        payment_id = f"pay_{rand_num}" if req.payment_method != "Cash on Delivery" else f"cod_{rand_num}"

        cursor.execute("""
        INSERT INTO orders (
            order_number, customer_id, customer_name, customer_phone, customer_email,
            order_date, delivery_date, delivery_slot, subtotal, delivery_fee,
            discount, gst, total_amount, payment_method, payment_status,
            payment_id, order_status, shipping_address, shipping_locality,
            shipping_pincode, delivery_notes, assigned_delivery_person_id,
            batch_id, tracking_timeline, delivery_latitude, delivery_longitude
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_number, customer_id, req.customer_name, req.customer_phone, req.customer_email,
            today_str, req.delivery_date, req.delivery_slot, subtotal, delivery_fee,
            discount, gst, total_amount, req.payment_method, payment_status,
            payment_id, order_status, req.shipping_address, req.shipping_locality,
            req.shipping_pincode, req.delivery_notes, del_person_id,
            batch_id, json.dumps(timeline), lat, lng
        ))
        order_id = cursor.lastrowid

        # Insert items
        for it in order_items_data:
            cursor.execute("""
            INSERT INTO order_items (order_id, product_id, variant_id, product_name, weight_label, unit_price, quantity, total_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (order_id, it["product_id"], it["variant_id"], it["name"], it["weight_label"], it["unit_price"], it["quantity"], it["total_price"]))

        # Notification & WhatsApp Simulation
        wa_message = f"🌱 *DJ Microgreens Order Confirmed!*\n\nHi {req.customer_name},\nOrder *#{order_number}* for ₹{total_amount:.2f} is confirmed!\n\n📅 Delivery: {req.delivery_date} ({req.delivery_slot})\n📍 Address: {req.shipping_address}, Chennai - {req.shipping_pincode}{map_line}\n\nOur team in Guindy farm will harvest your microgreens fresh on the morning of delivery.\n\nTrack order: {site_url(request)}/?track={order_number}\n\nQuestions? WhatsApp us at +91 99407 65140."
        cursor.execute("""
        INSERT INTO notifications (user_type, recipient_phone, recipient_email, notification_type, channel, title, message, status)
        VALUES ('Customer', ?, ?, 'Order Confirmation', 'WhatsApp', ?, ?, 'Delivered')
        """, (req.customer_phone, req.customer_email, f"Order #{order_number} Confirmed", wa_message))

        return {
            "success": True,
            "order_number": order_number,
            "order_id": order_id,
            "total_amount": total_amount,
            "status": order_status,
            "payment_status": payment_status,
            "whatsapp_message": wa_message,
            "message": "Order placed successfully! Fresh harvest scheduled."
        }

# ----------------- ORDER TRACKING -----------------
@router.get("/orders/track/{order_number}")
def track_order(order_number: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT o.*, d.name as delivery_person_name, d.phone as delivery_person_phone, d.vehicle_number
        FROM orders o
        LEFT JOIN delivery_personnel d ON o.assigned_delivery_person_id = d.id
        WHERE o.order_number = ?
        """, (order_number.strip(),))
        order = cursor.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_number} not found.")

        order_dict = dict(order)
        if order_dict["tracking_timeline"]:
            try:
                order_dict["tracking_timeline"] = json.loads(order_dict["tracking_timeline"])
            except:
                pass

        # Items
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_dict["id"],))
        order_dict["items"] = [dict(r) for r in cursor.fetchall()]

        return order_dict

# ----------------- CUSTOMER ORDERS & SUBSCRIPTIONS -----------------
# Customer orders and subscriptions are now under /api/account (signed-in customers only)

@router.post("/subscriptions")
def create_subscription(req: SubscriptionCreateRequest, request: Request):
    with get_db() as conn:
        cursor = conn.cursor()
        signed_in = current_customer(request, conn)
        if sign_in_enabled() and not signed_in:
            raise HTTPException(status_code=401, detail="Please log in to subscribe")
        if signed_in:
            if not phone_digits(signed_in.get("phone") or ""):
                raise HTTPException(status_code=400, detail="Please add your mobile number to your account first")
            req.customer_phone = signed_in["phone"]
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")

        # Calculate next delivery date
        next_date = (today + timedelta(days=3)).strftime("%Y-%m-%d")
        total_price = sum(item.get("price", 250) * item.get("qty", 1) for item in req.products)

        # Get/create customer
        if signed_in:
            cust = signed_in
        else:
            cursor.execute("SELECT id FROM customers WHERE phone = ?", (req.customer_phone.strip(),))
            cust = cursor.fetchone()
        if cust:
            customer_id = cust["id"]
        else:
            cursor.execute("""
            INSERT INTO customers (name, phone, email, address, pincode, customer_type)
            VALUES (?, ?, ?, ?, ?, 'Subscription')
            """, (req.customer_name, req.customer_phone.strip(), req.customer_email, req.shipping_address, req.shipping_pincode))
            customer_id = cursor.lastrowid

        cursor.execute("""
        INSERT INTO subscriptions (
            customer_id, customer_name, customer_phone, plan_type, frequency,
            delivery_day, delivery_slot, products_json, total_price_per_delivery,
            status, start_date, next_delivery_date, shipping_address, shipping_pincode
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?, ?, ?, ?)
        """, (
            customer_id, req.customer_name, req.customer_phone, req.plan_type, req.frequency,
            req.delivery_day, req.delivery_slot, json.dumps(req.products), total_price,
            today_str, next_date, req.shipping_address, req.shipping_pincode
        ))
        sub_id = cursor.lastrowid

        # Notification
        wa_msg = f"🌱 *DJ Microgreens Subscription Activated!*\n\nPlan: {req.plan_type} ({req.frequency})\nDelivery Day: {req.delivery_day} ({req.delivery_slot})\nNext Fresh Harvest: {next_date}\n\nManage your deliveries easily in your customer dashboard."
        cursor.execute("""
        INSERT INTO notifications (user_type, recipient_phone, recipient_email, notification_type, channel, title, message)
        VALUES ('Customer', ?, ?, 'Subscription Activated', 'WhatsApp', 'Subscription Confirmed', ?)
        """, (req.customer_phone, req.customer_email, wa_msg))

        return {"success": True, "subscription_id": sub_id, "message": "Subscription started successfully!"}

@router.post("/subscriptions/{sub_id}/toggle-status")
def toggle_subscription_status(sub_id: int, request: Request, action: str = Query(...)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,))
        sub = cursor.fetchone()
        if not sub:
            raise HTTPException(status_code=404, detail="Subscription not found")
        signed_in = current_customer(request, conn)
        if sign_in_enabled() and (not signed_in or signed_in["id"] != sub["customer_id"]):
            raise HTTPException(status_code=403, detail="Please sign in to manage your subscription")

        today_str = datetime.now().strftime("%Y-%m-%d")
        if action == "pause":
            cursor.execute("UPDATE subscriptions SET status = 'Paused', paused_at = ? WHERE id = ?", (today_str, sub_id))
        elif action == "resume":
            cursor.execute("UPDATE subscriptions SET status = 'Active', paused_at = NULL WHERE id = ?", (sub_id,))
        elif action == "cancel":
            cursor.execute("UPDATE subscriptions SET status = 'Cancelled' WHERE id = ?", (sub_id,))
        else:
            raise HTTPException(status_code=400, detail="Invalid action")

        return {"success": True, "status": action.capitalize()}
