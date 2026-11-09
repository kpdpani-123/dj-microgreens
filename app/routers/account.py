import json
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app.auth import IS_SECURE_COOKIE
from app.customer_auth import (
    CUSTOMER_COOKIE,
    CUSTOMER_SESSION_DAYS,
    OTP_MAX_ATTEMPTS,
    OTP_MAX_PER_HOUR,
    OTP_RESEND_WAIT_SECONDS,
    OTP_VALID_SECONDS,
    check_sms_otp,
    create_customer_token,
    current_customer,
    find_customer_by_phone,
    normalize_phone,
    otp_enabled,
    phone_digits,
    public_customer,
    send_sms_otp,
)
from app.database import get_db
from app.routers.admin import B2BOrderCreateRequest, place_b2b_order, wholesale_catalog

router = APIRouter(tags=["Customer Accounts"])


class PhoneRequest(BaseModel):
    phone: str


class VerifyRequest(BaseModel):
    phone: str
    otp: str


class ProfileRequest(BaseModel):
    name: str
    email: Optional[str] = ""
    address: str
    locality: Optional[str] = ""
    pincode: str


class ChefOrderRequest(BaseModel):
    delivery_date: str
    delivery_slot: str = "Morning (7:00 AM - 9:00 AM)"
    items: List[Dict[str, Any]]
    notes: Optional[str] = ""


def require_customer(request: Request, conn) -> dict:
    customer = current_customer(request, conn)
    if not customer:
        raise HTTPException(status_code=401, detail="Please sign in with your phone number")
    return customer


# ----------------- SIGN IN WITH PHONE + OTP -----------------
@router.get("/api/account/status")
def account_status(request: Request):
    with get_db() as conn:
        customer = current_customer(request, conn)
    return {"otp_enabled": otp_enabled(), "customer": public_customer(customer) if customer else None}


@router.post("/api/account/send-otp")
def send_otp(req: PhoneRequest):
    if not otp_enabled():
        raise HTTPException(status_code=503, detail="Phone sign-in is not switched on yet")
    digits = phone_digits(req.phone)
    if not digits:
        raise HTTPException(status_code=400, detail="Enter a valid 10-digit mobile number")
    now = time.time()
    with get_db() as conn:
        recent = conn.execute(
            "SELECT created_at FROM otp_requests WHERE phone = ? AND created_at > ? ORDER BY created_at DESC",
            (digits, now - 3600),
        ).fetchall()
        if recent and now - recent[0]["created_at"] < OTP_RESEND_WAIT_SECONDS:
            raise HTTPException(status_code=429, detail="Please wait 30 seconds before asking for another OTP")
        if len(recent) >= OTP_MAX_PER_HOUR:
            raise HTTPException(status_code=429, detail="Too many OTP requests. Please try again in an hour")
    try:
        session_id = send_sms_otp(digits)
    except RuntimeError:
        raise HTTPException(status_code=502, detail="Could not send the OTP right now. Please try again shortly")
    with get_db() as conn:
        conn.execute("INSERT INTO otp_requests (phone, session_id, created_at) VALUES (?, ?, ?)", (digits, session_id, now))
    return {"success": True, "message": f"OTP sent to +91 {digits[:5]} {digits[5:]}"}


@router.post("/api/account/verify-otp")
def verify_otp(req: VerifyRequest, response: Response):
    if not otp_enabled():
        raise HTTPException(status_code=503, detail="Phone sign-in is not switched on yet")
    digits = phone_digits(req.phone)
    otp = "".join(ch for ch in req.otp if ch.isdigit())
    if not digits or not (4 <= len(otp) <= 8):
        raise HTTPException(status_code=400, detail="Enter the OTP from the SMS")
    with get_db() as conn:
        pending = conn.execute(
            "SELECT * FROM otp_requests WHERE phone = ? AND verified = 0 AND created_at > ? ORDER BY created_at DESC LIMIT 1",
            (digits, time.time() - OTP_VALID_SECONDS),
        ).fetchone()
        if not pending:
            raise HTTPException(status_code=400, detail="This OTP has expired. Please ask for a new one")
        if pending["attempts"] >= OTP_MAX_ATTEMPTS:
            raise HTTPException(status_code=429, detail="Too many wrong tries. Please ask for a new OTP")
        conn.execute("UPDATE otp_requests SET attempts = attempts + 1 WHERE id = ?", (pending["id"],))
        session_id, request_id = pending["session_id"], pending["id"]

    if not check_sms_otp(session_id, otp):
        raise HTTPException(status_code=400, detail="Wrong OTP. Please check the SMS and try again")

    with get_db() as conn:
        conn.execute("UPDATE otp_requests SET verified = 1 WHERE id = ?", (request_id,))
        customer = find_customer_by_phone(conn, digits)
        if customer:
            conn.execute("UPDATE customers SET phone = ? WHERE id = ?", (normalize_phone(digits), customer["id"]))
            customer["phone"] = normalize_phone(digits)
        else:
            cur = conn.execute(
                "INSERT INTO customers (name, phone, customer_type, total_orders, lifetime_value, status) VALUES ('', ?, 'Retail', 0, 0, 'Active')",
                (normalize_phone(digits),),
            )
            customer = dict(conn.execute("SELECT * FROM customers WHERE id = ?", (cur.lastrowid,)).fetchone())

    response.set_cookie(
        CUSTOMER_COOKIE, create_customer_token(customer["id"]), max_age=CUSTOMER_SESSION_DAYS * 86400,
        httponly=True, samesite="lax", secure=IS_SECURE_COOKIE,
    )
    return {"success": True, "customer": public_customer(customer)}


@router.post("/api/account/logout")
def customer_logout(response: Response):
    response.delete_cookie(CUSTOMER_COOKIE)
    return {"success": True}


@router.post("/api/account/profile")
def save_profile(req: ProfileRequest, request: Request):
    name, address, pincode = req.name.strip(), req.address.strip(), req.pincode.strip()
    if not name or not address:
        raise HTTPException(status_code=400, detail="Name and address are required")
    if not (len(pincode) == 6 and pincode.isdigit()):
        raise HTTPException(status_code=400, detail="Enter a 6-digit pincode")
    with get_db() as conn:
        customer = require_customer(request, conn)
        conn.execute(
            "UPDATE customers SET name = ?, email = ?, address = ?, locality = ?, pincode = ? WHERE id = ?",
            (name, (req.email or "").strip(), address, (req.locality or "").strip(), pincode, customer["id"]),
        )
        updated = dict(conn.execute("SELECT * FROM customers WHERE id = ?", (customer["id"],)).fetchone())
    return {"success": True, "customer": public_customer(updated)}


@router.get("/api/account/orders")
def my_orders(request: Request):
    with get_db() as conn:
        customer = require_customer(request, conn)
        orders = [dict(r) for r in conn.execute(
            "SELECT * FROM orders WHERE customer_id = ? ORDER BY id DESC", (customer["id"],)
        ).fetchall()]
        for o in orders:
            try:
                o["tracking_timeline"] = json.loads(o["tracking_timeline"] or "[]")
            except Exception:
                pass
            o["items"] = [dict(r) for r in conn.execute("SELECT * FROM order_items WHERE order_id = ?", (o["id"],)).fetchall()]
    return orders


@router.get("/api/account/subscriptions")
def my_subscriptions(request: Request):
    with get_db() as conn:
        customer = require_customer(request, conn)
        subs = [dict(r) for r in conn.execute(
            "SELECT * FROM subscriptions WHERE customer_id = ? ORDER BY id DESC", (customer["id"],)
        ).fetchall()]
    for s in subs:
        try:
            s["products_json"] = json.loads(s["products_json"])
        except Exception:
            pass
    return subs


# ----------------- CHEF ORDERING PORTAL (/b2b) -----------------
@router.get("/api/b2b/catalog")
def b2b_catalog():
    with get_db() as conn:
        return {"wholesale_catalog": wholesale_catalog(conn)}


@router.post("/api/b2b/orders")
def chef_place_order(req: ChefOrderRequest, request: Request):
    with get_db() as conn:
        customer = require_customer(request, conn)
    if not public_customer(customer)["is_chef"]:
        raise HTTPException(status_code=403, detail="This phone number is not registered as a chef account")
    if not req.items:
        raise HTTPException(status_code=400, detail="Please select at least one item")
    try:
        datetime.strptime(req.delivery_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Choose a delivery date")

    # Use the server's wholesale prices, never prices sent by the browser
    with get_db() as conn:
        prices = {(c["name"], c["weight_label"]): c["wholesale_price"] for c in wholesale_catalog(conn)}
    items = []
    for it in req.items:
        key = (str(it.get("name", "")), str(it.get("weight", "")))
        try:
            qty = int(it.get("qty", 0))
        except (TypeError, ValueError):
            qty = 0
        if key not in prices or not (1 <= qty <= 500):
            raise HTTPException(status_code=400, detail=f"Unknown item or quantity: {key[0]} {key[1]}")
        items.append({"name": key[0], "weight": key[1], "price": prices[key], "qty": qty})

    order = B2BOrderCreateRequest(
        customer_id=customer["id"], delivery_date=req.delivery_date, delivery_slot=req.delivery_slot,
        credit_terms=customer.get("credit_terms") or "Net 15", items=items, notes=req.notes or "",
    )
    return place_b2b_order(order)
