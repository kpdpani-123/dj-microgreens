import hmac
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
    clean_email,
    create_customer_token,
    current_customer,
    find_customer_by_phone,
    google_client_id,
    hash_code,
    mask_email,
    new_code,
    normalize_phone,
    otp_enabled,
    phone_digits,
    public_customer,
    send_email_code,
    sign_in_enabled,
    verify_google_credential,
)
from app.database import get_db
from app.routers.admin import B2BOrderCreateRequest, place_b2b_order, wholesale_catalog

router = APIRouter(tags=["Customer Accounts"])


class PhoneRequest(BaseModel):
    phone: str
    email: Optional[str] = ""


class GoogleRequest(BaseModel):
    credential: str


class VerifyRequest(BaseModel):
    phone: str
    otp: str


class ProfileRequest(BaseModel):
    phone: Optional[str] = None
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
        raise HTTPException(status_code=401, detail="Please log in first")
    return customer


# ----------------- SIGN IN: PHONE NUMBER + CODE SENT BY EMAIL -----------------
@router.get("/api/account/status")
def account_status(request: Request):
    with get_db() as conn:
        customer = current_customer(request, conn)
    return {
        "sign_in_enabled": sign_in_enabled(),
        "google_client_id": google_client_id(),
        "otp_enabled": otp_enabled(),
        "customer": public_customer(customer) if customer else None,
    }


def _set_customer_cookie(response: Response, customer_id: int):
    response.set_cookie(
        CUSTOMER_COOKIE, create_customer_token(customer_id), max_age=CUSTOMER_SESSION_DAYS * 86400,
        httponly=True, samesite="lax", secure=IS_SECURE_COOKIE,
    )


@router.post("/api/account/google")
def google_sign_in(req: GoogleRequest, response: Response):
    """Log in or sign up with a Google account. New customers add their phone number afterwards."""
    if not google_client_id():
        raise HTTPException(status_code=503, detail="Google sign-in is not switched on yet")
    try:
        g = verify_google_credential(req.credential)
    except ValueError as e:
        if str(e) == "unreachable":
            raise HTTPException(status_code=502, detail="Could not reach Google. Please try again")
        raise HTTPException(status_code=401, detail="Google sign-in failed. Please try again")
    with get_db() as conn:
        row = conn.execute("SELECT * FROM customers WHERE google_sub = ? ORDER BY id LIMIT 1", (g["sub"],)).fetchone()
        if not row:
            # Same Gmail already on file (an earlier sign-in, or a chef the admin added): use that account
            matches = [dict(r) for r in conn.execute(
                "SELECT * FROM customers WHERE LOWER(TRIM(email)) = ? ORDER BY id", (g["email"],)).fetchall()]
            matches.sort(key=lambda c: (c.get("status") == "Removed", not public_customer(c)["is_chef"], c["id"]))
            row = matches[0] if matches else None
        if row:
            customer = dict(row)
            conn.execute(
                "UPDATE customers SET google_sub = ?, email = ?, name = CASE WHEN TRIM(COALESCE(name, '')) = '' THEN ? ELSE name END WHERE id = ?",
                (g["sub"], g["email"], g["name"], customer["id"]),
            )
        else:
            cur = conn.execute(
                "INSERT INTO customers (name, phone, email, google_sub, customer_type, total_orders, lifetime_value, status) "
                "VALUES (?, ?, ?, ?, 'Retail', 0, 0, 'Active')",
                # phone must be unique and filled; a placeholder holds the place until they add their number
                (g["name"], f"pending:{g['sub']}", g["email"], g["sub"]),
            )
            customer = {"id": cur.lastrowid}
        customer = dict(conn.execute("SELECT * FROM customers WHERE id = ?", (customer["id"],)).fetchone())
    _set_customer_cookie(response, customer["id"])
    return {"success": True, "customer": public_customer(customer)}


@router.post("/api/account/send-otp")
def send_otp(req: PhoneRequest):
    if not otp_enabled():
        raise HTTPException(status_code=503, detail="Sign-in is not switched on yet")
    digits = phone_digits(req.phone)
    if not digits:
        raise HTTPException(status_code=400, detail="Enter a valid 10-digit mobile number")
    now = time.time()
    with get_db() as conn:
        customer = find_customer_by_phone(conn, digits)
        saved_email = clean_email(customer.get("email")) if customer else None
        # A number that already has an email always gets its code there,
        # so nobody can take over an account by typing a different email.
        email = saved_email or clean_email(req.email)
        if not email:
            raise HTTPException(status_code=400, detail="Enter a valid email address")
        recent = conn.execute(
            "SELECT created_at FROM otp_requests WHERE (phone = ? OR email = ?) AND created_at > ? ORDER BY created_at DESC",
            (digits, email, now - 3600),
        ).fetchall()
        if recent and now - recent[0]["created_at"] < OTP_RESEND_WAIT_SECONDS:
            raise HTTPException(status_code=429, detail="Please wait 30 seconds before asking for another code")
        if len(recent) >= OTP_MAX_PER_HOUR:
            raise HTTPException(status_code=429, detail="Too many code requests. Please try again in an hour")
        request_key = new_code() + new_code()
        code = new_code()
        # Only a keyed hash of the code is stored
        cur = conn.execute(
            "INSERT INTO otp_requests (phone, email, session_id, created_at) VALUES (?, ?, ?, ?)",
            (digits, email, f"{request_key}:{hash_code(code, request_key)}", now),
        )
        request_id = cur.lastrowid
    try:
        send_email_code(email, code)
    except RuntimeError:
        with get_db() as conn:
            conn.execute("DELETE FROM otp_requests WHERE id = ?", (request_id,))
        raise HTTPException(status_code=502, detail="Could not send the email right now. Please try again shortly")
    shown = mask_email(email) if saved_email else email
    note = " (the email saved on this account)" if saved_email and saved_email != clean_email(req.email) else ""
    return {"success": True, "sent_to": shown, "message": f"Code sent to {shown}{note}"}


@router.post("/api/account/verify-otp")
def verify_otp(req: VerifyRequest, response: Response):
    if not otp_enabled():
        raise HTTPException(status_code=503, detail="Sign-in is not switched on yet")
    digits = phone_digits(req.phone)
    code = "".join(ch for ch in req.otp if ch.isdigit())
    if not digits or len(code) != 6:
        raise HTTPException(status_code=400, detail="Enter the 6-digit code from the email")
    with get_db() as conn:
        pending = conn.execute(
            "SELECT * FROM otp_requests WHERE phone = ? AND verified = 0 AND created_at > ? ORDER BY created_at DESC LIMIT 1",
            (digits, time.time() - OTP_VALID_SECONDS),
        ).fetchone()
        if not pending:
            raise HTTPException(status_code=400, detail="This code has expired. Please ask for a new one")
        if pending["attempts"] >= OTP_MAX_ATTEMPTS:
            raise HTTPException(status_code=429, detail="Too many wrong tries. Please ask for a new code")
        # Count the try in its own step, so a wrong code cannot undo the count
        conn.execute("UPDATE otp_requests SET attempts = attempts + 1 WHERE id = ?", (pending["id"],))
        pending = dict(pending)

    request_key, _, expected = (pending["session_id"] or "").partition(":")
    if not expected or not hmac.compare_digest(hash_code(code, request_key), expected):
        raise HTTPException(status_code=400, detail="Wrong code. Please check the email and try again")

    with get_db() as conn:
        # Mark used only if still unused, so the same code cannot sign in twice
        used = conn.execute("UPDATE otp_requests SET verified = 1 WHERE id = ? AND verified = 0", (pending["id"],))
        if getattr(used, "rowcount", 1) == 0:
            raise HTTPException(status_code=400, detail="This code has already been used. Please ask for a new one")
        email = pending["email"]
        customer = find_customer_by_phone(conn, digits)
        if customer:
            new_email = customer.get("email") if clean_email(customer.get("email")) else email
            conn.execute("UPDATE customers SET phone = ?, email = ? WHERE id = ?",
                         (normalize_phone(digits), new_email, customer["id"]))
            customer.update(phone=normalize_phone(digits), email=new_email)
        else:
            cur = conn.execute(
                "INSERT INTO customers (name, phone, email, customer_type, total_orders, lifetime_value, status) VALUES ('', ?, ?, 'Retail', 0, 0, 'Active')",
                (normalize_phone(digits), email),
            )
            customer = dict(conn.execute("SELECT * FROM customers WHERE id = ?", (cur.lastrowid,)).fetchone())

    _set_customer_cookie(response, customer["id"])
    return {"success": True, "customer": public_customer(customer)}


@router.post("/api/account/logout")
def customer_logout(response: Response):
    response.delete_cookie(CUSTOMER_COOKIE)
    return {"success": True}


@router.post("/api/account/profile")
def save_profile(req: ProfileRequest, request: Request, response: Response):
    name, address, pincode = req.name.strip(), req.address.strip(), req.pincode.strip()
    if not name or not address:
        raise HTTPException(status_code=400, detail="Name and address are required")
    if not (len(pincode) == 6 and pincode.isdigit()):
        raise HTTPException(status_code=400, detail="Enter a 6-digit pincode")
    with get_db() as conn:
        customer = require_customer(request, conn)
        phone = customer.get("phone") or ""
        if req.phone is not None and phone_digits(req.phone) != phone_digits(phone):
            digits = phone_digits(req.phone)
            if not digits:
                raise HTTPException(status_code=400, detail="Enter a valid 10-digit mobile number")
            other = find_customer_by_phone(conn, digits)
            if other and other["id"] != customer["id"]:
                if public_customer(other)["is_chef"]:
                    raise HTTPException(status_code=409, detail="This number belongs to a chef account. Please ask DJ Microgreens to add your Gmail to it, then log in again")
                if other.get("google_sub") or clean_email(other.get("email")):
                    raise HTTPException(status_code=409, detail="This number is already linked to another account. Please contact DJ Microgreens on +91 99407 65140")
                # An earlier guest order with this number: join it to this login so its order history carries over
                for table in ("orders", "subscriptions"):
                    conn.execute(f"UPDATE {table} SET customer_id = ? WHERE customer_id = ?", (other["id"], customer["id"]))
                conn.execute("UPDATE customers SET google_sub = NULL, email = '' WHERE id = ?", (customer["id"],))
                conn.execute("UPDATE customers SET google_sub = ?, email = ? WHERE id = ?",
                             (customer.get("google_sub"), customer.get("email") or "", other["id"]))
                conn.execute("DELETE FROM customers WHERE id = ?", (customer["id"],))
                customer = dict(conn.execute("SELECT * FROM customers WHERE id = ?", (other["id"],)).fetchone())
                _set_customer_cookie(response, customer["id"])
            phone = normalize_phone(digits)
        if not phone_digits(phone):
            raise HTTPException(status_code=400, detail="Enter a valid 10-digit mobile number")
        conn.execute(
            "UPDATE customers SET phone = ?, name = ?, address = ?, locality = ?, pincode = ? WHERE id = ?",
            (phone, name, address, (req.locality or "").strip(), pincode, customer["id"]),
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
        raise HTTPException(status_code=403, detail="This account is not registered as a chef account")
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
