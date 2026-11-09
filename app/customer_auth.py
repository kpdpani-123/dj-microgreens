"""Customer and chef login by phone number + SMS OTP (sent by 2Factor.in)."""
import base64
import hashlib
import hmac
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

CUSTOMER_COOKIE = "dj_customer"
CUSTOMER_SESSION_DAYS = 30
B2B_TYPES = ("Hotel", "Restaurant", "Cafe")

OTP_VALID_SECONDS = 10 * 60
OTP_RESEND_WAIT_SECONDS = 30
OTP_MAX_PER_HOUR = 5
OTP_MAX_ATTEMPTS = 5


# ----------------- PHONE NUMBERS -----------------
def phone_digits(phone: str) -> Optional[str]:
    """The 10-digit Indian mobile number, or None. Accepts +91, 91 or 0 in front."""
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if len(digits) == 10 and digits[0] in "6789":
        return digits
    return None


def normalize_phone(phone: str) -> Optional[str]:
    """'09940765140' -> '+91 99407 65140'."""
    d = phone_digits(phone)
    return f"+91 {d[:5]} {d[5:]}" if d else None


def find_customer_by_phone(conn, phone: str) -> Optional[dict]:
    """Find a customer whatever way their phone number was typed."""
    target = phone_digits(phone)
    if not target:
        return None
    for row in conn.execute("SELECT * FROM customers ORDER BY id").fetchall():
        if phone_digits(row["phone"]) == target:
            return dict(row)
    return None


# ----------------- 2FACTOR.IN SMS OTP -----------------
def otp_enabled() -> bool:
    return bool(os.environ.get("TWOFACTOR_API_KEY"))


def _twofactor_get(path: str) -> dict:
    key = os.environ.get("TWOFACTOR_API_KEY", "")
    url = f"https://2factor.in/API/V1/{urllib.parse.quote(key)}/{path}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "dj-microgreens"}), timeout=15) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode() or "{}")
        except Exception:
            return {"Status": "Error", "Details": f"HTTP {e.code}"}
    except Exception as e:
        return {"Status": "Error", "Details": str(e)}


def send_sms_otp(digits: str) -> str:
    """Ask 2Factor to text an OTP. Returns their session id, raises RuntimeError on failure."""
    template = os.environ.get("TWOFACTOR_TEMPLATE", "").strip()
    path = f"SMS/{digits}/AUTOGEN" + (f"/{urllib.parse.quote(template)}" if template else "")
    data = _twofactor_get(path)
    if data.get("Status") != "Success" or not data.get("Details"):
        print(f"2Factor send failed: {data}")
        raise RuntimeError(str(data.get("Details") or "SMS service error"))
    return data["Details"]


def check_sms_otp(session_id: str, otp: str) -> bool:
    data = _twofactor_get(f"SMS/VERIFY/{urllib.parse.quote(session_id)}/{urllib.parse.quote(otp)}")
    return data.get("Status") == "Success" and "match" in str(data.get("Details", "")).lower()


# ----------------- CUSTOMER SESSIONS -----------------
def _sign(payload: str) -> str:
    from app.auth import get_secret_key
    return hmac.new(get_secret_key().encode(), f"customer:{payload}".encode(), hashlib.sha256).hexdigest()


def create_customer_token(customer_id: int) -> str:
    expires = int(time.time()) + CUSTOMER_SESSION_DAYS * 86400
    payload = f"{customer_id}:{expires}"
    return base64.urlsafe_b64encode(f"{payload}:{_sign(payload)}".encode()).decode()


def customer_id_from_token(token: Optional[str]) -> Optional[int]:
    if not token:
        return None
    try:
        customer_id, expires, sig = base64.urlsafe_b64decode(token.encode()).decode().split(":")
    except Exception:
        return None
    if not hmac.compare_digest(sig, _sign(f"{customer_id}:{expires}")) or int(expires) < time.time():
        return None
    return int(customer_id)


def current_customer(request, conn) -> Optional[dict]:
    cid = customer_id_from_token(request.cookies.get(CUSTOMER_COOKIE))
    if cid is None:
        return None
    row = conn.execute("SELECT * FROM customers WHERE id = ?", (cid,)).fetchone()
    return dict(row) if row else None


def public_customer(c: dict) -> dict:
    is_chef = c.get("customer_type") in B2B_TYPES and c.get("status") != "Removed"
    return {
        "id": c["id"],
        "name": c.get("name") or "",
        "phone": c.get("phone") or "",
        "email": c.get("email") or "",
        "address": c.get("address") or "",
        "locality": c.get("locality") or "",
        "pincode": c.get("pincode") or "",
        "customer_type": c.get("customer_type") or "Retail",
        "credit_terms": c.get("credit_terms") or "Net 15",
        "is_chef": is_chef,
        "profile_complete": bool((c.get("name") or "").strip() and (c.get("address") or "").strip() and (c.get("pincode") or "").strip()),
    }


def site_url(request) -> str:
    """The site's own address, for links in WhatsApp messages."""
    url = str(request.base_url).rstrip("/")
    host = request.url.hostname or ""
    if url.startswith("http://") and host not in ("localhost", "127.0.0.1"):
        url = "https://" + url[len("http://"):]
    return url
