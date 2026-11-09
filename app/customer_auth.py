"""Customer and chef login: "Continue with Google", or a code sent to their email from the shop's Gmail."""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import smtplib
import time
import urllib.parse
import urllib.request
from email.message import EmailMessage
from email.utils import formataddr
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
    if (phone or "").startswith("pending:"):  # Google sign-up that has not added a number yet
        return None
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


# ----------------- CONTINUE WITH GOOGLE -----------------
GOOGLE_ISSUERS = ("accounts.google.com", "https://accounts.google.com")


def google_client_id() -> str:
    return os.environ.get("GOOGLE_CLIENT_ID", "").strip()


def sign_in_enabled() -> bool:
    """Customers must sign in to order once any sign-in method is set up."""
    return bool(google_client_id()) or otp_enabled()


def _google_tokeninfo(credential: str) -> dict:
    url = "https://oauth2.googleapis.com/tokeninfo?" + urllib.parse.urlencode({"id_token": credential})
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "dj-microgreens"}), timeout=15) as resp:
        return json.loads(resp.read().decode() or "{}")


def verify_google_credential(credential: str) -> dict:
    """Check a Google sign-in token. Returns {sub, email, name}; raises ValueError if it is not valid for this site."""
    client_id = google_client_id()
    if not client_id or not credential or len(credential) > 5000:
        raise ValueError("missing")
    try:
        info = _google_tokeninfo(credential)
    except Exception as e:
        print(f"Google token check failed: {e!r}")
        raise ValueError("unreachable")
    email = clean_email(info.get("email"))
    try:
        expires = int(info.get("exp", 0))
    except (TypeError, ValueError):
        expires = 0
    if (info.get("aud") != client_id or info.get("iss") not in GOOGLE_ISSUERS or not info.get("sub")
            or not email or str(info.get("email_verified")).lower() != "true" or expires < time.time()):
        raise ValueError("invalid")
    return {"sub": str(info["sub"]), "email": email, "name": (info.get("name") or "").strip()}


# ----------------- EMAIL CODES (sent from Gmail) -----------------
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def otp_enabled() -> bool:
    """Sign-in is on once the Gmail address and its app password are set in Vercel."""
    return bool(os.environ.get("GMAIL_ADDRESS") and os.environ.get("GMAIL_APP_PASSWORD"))


def clean_email(email: str) -> Optional[str]:
    email = (email or "").strip().lower()
    return email if EMAIL_RE.match(email) and len(email) <= 254 else None


def mask_email(email: str) -> str:
    """'kpdandapani@gmail.com' -> 'kp*******@gmail.com'."""
    name, _, domain = (email or "").partition("@")
    return f"{name[:2]}{'*' * max(len(name) - 2, 1)}@{domain}"


def new_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_code(code: str, request_key: str) -> str:
    from app.auth import get_secret_key
    return hmac.new(get_secret_key().encode(), f"code:{request_key}:{code}".encode(), hashlib.sha256).hexdigest()


def send_email_code(to_email: str, code: str) -> None:
    """Email the sign-in code from the shop's Gmail. Raises RuntimeError on failure."""
    sender = os.environ.get("GMAIL_ADDRESS", "").strip()
    password = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    msg = EmailMessage()
    msg["Subject"] = f"{code} is your DJ Microgreens sign-in code"
    msg["From"] = formataddr(("DJ Microgreens", sender))
    msg["To"] = to_email
    msg.set_content(
        f"Your DJ Microgreens sign-in code is {code}\n\n"
        f"It works for {OTP_VALID_SECONDS // 60} minutes. If you did not ask for it, you can ignore this email.\n\n"
        "DJ Microgreens, Chennai\nK.P Dandapani · +91 99407 65140"
    )
    msg.add_alternative(f"""<div style="font-family:Arial,sans-serif;color:#0f172a">
<p>Your DJ Microgreens sign-in code is</p>
<p style="font-size:28px;font-weight:bold;letter-spacing:6px;color:#14532d">{code}</p>
<p>It works for {OTP_VALID_SECONDS // 60} minutes. If you did not ask for it, you can ignore this email.</p>
<p style="color:#64748b;font-size:12px">DJ Microgreens, Chennai<br>K.P Dandapani · +91 99407 65140</p></div>""", subtype="html")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Gmail send failed: {e!r}")
        raise RuntimeError("email service error")


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
        "phone": normalize_phone(c.get("phone") or "") or "",
        "email": c.get("email") or "",
        "address": c.get("address") or "",
        "locality": c.get("locality") or "",
        "pincode": c.get("pincode") or "",
        "customer_type": c.get("customer_type") or "Retail",
        "credit_terms": c.get("credit_terms") or "Net 15",
        "is_chef": is_chef,
        "profile_complete": bool(phone_digits(c.get("phone") or "") and (c.get("name") or "").strip()
                                 and (c.get("address") or "").strip() and (c.get("pincode") or "").strip()),
    }


def site_url(request) -> str:
    """The site's own address, for links in WhatsApp messages."""
    url = str(request.base_url).rstrip("/")
    host = request.url.hostname or ""
    if url.startswith("http://") and host not in ("localhost", "127.0.0.1"):
        url = "https://" + url[len("http://"):]
    return url
