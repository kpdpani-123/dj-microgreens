"""Staff login: password hashing, signed session cookies and role access rules."""
import base64
import hashlib
import hmac
import os
import secrets
import time
from typing import Optional

from app.database import get_db

SESSION_COOKIE = "dj_session"
SESSION_MAX_AGE = 60 * 60 * 12  # 12 hours
IS_SECURE_COOKIE = bool(os.environ.get("VERCEL"))  # HTTPS-only cookie on Vercel

# Set DJ_SECRET_KEY in Vercel (Project → Settings → Environment Variables) for production.
SECRET_KEY = os.environ.get("DJ_SECRET_KEY", "dj-microgreens-change-this-secret-key")

DEFAULT_PASSWORD = "DJmicro@2026"

# username, role, full name, phone
DEFAULT_STAFF = [
    ("superadmin", "Super Admin", "K.P Dandapani", "+91 99407 65140"),
    ("operations", "Operations Manager", "P. Jayanthi", ""),
    ("farm", "Farm Manager", "", ""),
    ("inventory", "Inventory Manager", "", ""),
    ("delivery", "Delivery Manager", "", ""),
    ("sales", "Sales & B2B Manager", "", ""),
]

ALL_TABS = ["overview", "orders", "production", "inventory", "crm", "b2b", "delivery", "finance"]

# Which admin dashboard tabs each role can open
ROLE_TABS = {
    "Super Admin": ALL_TABS,
    "Operations Manager": ["overview", "orders", "production", "inventory", "crm", "b2b", "delivery"],
    "Farm Manager": ["production", "inventory"],
    "Inventory Manager": ["inventory", "production"],
    "Delivery Manager": ["orders", "delivery"],
    "Sales & B2B Manager": ["orders", "crm", "b2b"],
}

# API path prefix -> tab that grants access to it
API_TAB_RULES = [
    ("/api/admin/dashboard-stats", ["overview"]),
    ("/api/admin/orders", ["orders"]),
    ("/api/admin/production", ["production"]),
    ("/api/admin/inventory", ["inventory"]),
    ("/api/admin/crm", ["crm"]),
    ("/api/admin/delivery", ["delivery"]),
    ("/api/admin/finance", ["finance"]),
    ("/api/exports", ["overview", "orders", "finance"]),
]


# ----------------- PASSWORDS -----------------
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
    return f"pbkdf2${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt, digest = stored.split("$")
    except (ValueError, AttributeError):
        return False
    if scheme != "pbkdf2":
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
    return hmac.compare_digest(check, digest)


# ----------------- SESSIONS -----------------
def _sign(payload: str) -> str:
    return hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()


def create_session_token(user_id: int, password_hash: str) -> str:
    expires = int(time.time()) + SESSION_MAX_AGE
    # Tie the session to the current password so changing it signs out old sessions
    pw_tag = hashlib.sha256(password_hash.encode()).hexdigest()[:12]
    payload = f"{user_id}:{expires}:{pw_tag}"
    raw = f"{payload}:{_sign(payload)}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def get_user_from_token(token: Optional[str]) -> Optional[dict]:
    if not token:
        return None
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        user_id, expires, pw_tag, sig = raw.split(":")
    except Exception:
        return None
    payload = f"{user_id}:{expires}:{pw_tag}"
    if not hmac.compare_digest(sig, _sign(payload)) or int(expires) < time.time():
        return None

    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ? AND is_active = 1", (int(user_id),)
        ).fetchone()
    if not row or row["role"] not in ROLE_TABS:
        return None
    if hashlib.sha256(row["password_hash"].encode()).hexdigest()[:12] != pw_tag:
        return None
    return dict(row)


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "full_name": user["full_name"],
        "phone": user.get("phone") or "",
        "must_change_password": bool(user.get("must_change_password")),
        "tabs": ROLE_TABS.get(user["role"], []),
    }


def required_tabs_for_path(path: str) -> Optional[list]:
    """Tabs that allow access to this API path, or None if the path is not staff-only."""
    # The public chef ordering portal (/b2b) uses these two endpoints
    if path.startswith("/api/admin/b2b"):
        return None
    for prefix, tabs in API_TAB_RULES:
        if path.startswith(prefix):
            return tabs
    if path.startswith("/api/admin"):
        return ALL_TABS
    return None


# ----------------- DEFAULT ACCOUNTS -----------------
def ensure_staff_accounts():
    """Create the staff logins. Replaces the old demo users (plain-text passwords) once."""
    with get_db() as conn:
        cur = conn.cursor()
        cols = [r["name"] for r in cur.execute("PRAGMA table_info(users)").fetchall()]
        if "must_change_password" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER DEFAULT 0")

        rows = cur.execute("SELECT password_hash FROM users").fetchall()
        has_old_demo_users = any(not (r["password_hash"] or "").startswith("pbkdf2$") for r in rows)
        if rows and not has_old_demo_users:
            return

        cur.execute("DELETE FROM users")
        for username, role, full_name, phone in DEFAULT_STAFF:
            cur.execute(
                """INSERT INTO users (username, password_hash, role, full_name, email, phone, must_change_password)
                   VALUES (?, ?, ?, ?, '', ?, 1)""",
                (username, hash_password(DEFAULT_PASSWORD), role, full_name, phone),
            )
