from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app.auth import (
    IS_SECURE_COOKIE,
    SESSION_COOKIE,
    SESSION_MAX_AGE,
    create_session_token,
    get_user_from_token,
    hash_password,
    public_user,
    verify_password,
)
from app.database import get_db

router = APIRouter(prefix="/api/auth", tags=["Staff Login"])


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangeCredentialsRequest(BaseModel):
    current_password: str
    new_username: Optional[str] = None
    new_password: Optional[str] = None
    full_name: Optional[str] = None


class AdminUpdateUserRequest(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    new_password: Optional[str] = None


def current_user(request: Request) -> dict:
    user = get_user_from_token(request.cookies.get(SESSION_COOKIE))
    if not user:
        raise HTTPException(status_code=401, detail="Please sign in")
    return user


def _set_session(response: Response, user: dict):
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(user["id"], user["password_hash"]),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=IS_SECURE_COOKIE,
    )


def _validate_username(conn, username: str, user_id: int) -> str:
    username = username.strip()
    if len(username) < 3 or " " in username:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters with no spaces")
    taken = conn.execute(
        "SELECT id FROM users WHERE lower(username) = lower(?) AND id != ?", (username, user_id)
    ).fetchone()
    if taken:
        raise HTTPException(status_code=400, detail="That username is already taken")
    return username


def _validate_password(password: str):
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")


@router.post("/login")
def login(req: LoginRequest, response: Response):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE lower(username) = lower(?) AND is_active = 1",
            (req.username.strip(),),
        ).fetchone()
    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Wrong username or password")
    user = dict(row)
    _set_session(response, user)
    return {"success": True, "user": public_user(user)}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)
    return {"success": True}


@router.get("/me")
def me(request: Request):
    return public_user(current_user(request))


@router.post("/change-credentials")
def change_credentials(req: ChangeCredentialsRequest, request: Request, response: Response):
    user = current_user(request)
    if not verify_password(req.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is wrong")

    with get_db() as conn:
        username = user["username"]
        if req.new_username and req.new_username.strip() != user["username"]:
            username = _validate_username(conn, req.new_username, user["id"])

        password_hash = user["password_hash"]
        must_change = user.get("must_change_password") or 0
        if req.new_password:
            _validate_password(req.new_password)
            password_hash = hash_password(req.new_password)
            must_change = 0

        full_name = user["full_name"] if req.full_name is None else req.full_name.strip()

        conn.execute(
            "UPDATE users SET username = ?, password_hash = ?, full_name = ?, must_change_password = ? WHERE id = ?",
            (username, password_hash, full_name, must_change, user["id"]),
        )
        updated = dict(conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone())

    # Re-issue the session so the user stays signed in after a password change
    _set_session(response, updated)
    return {"success": True, "user": public_user(updated)}


# ----------------- SUPER ADMIN: MANAGE STAFF LOGINS -----------------
def _require_super_admin(request: Request) -> dict:
    user = current_user(request)
    if user["role"] != "Super Admin":
        raise HTTPException(status_code=403, detail="Only the Super Admin can manage staff logins")
    return user


@router.get("/users")
def list_users(request: Request):
    _require_super_admin(request)
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    return [public_user(dict(r)) for r in rows]


@router.post("/users/{user_id}")
def update_user(user_id: int, req: AdminUpdateUserRequest, request: Request):
    _require_super_admin(request)
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        user = dict(row)

        username = user["username"]
        if req.username and req.username.strip() != user["username"]:
            username = _validate_username(conn, req.username, user_id)

        full_name = user["full_name"] if req.full_name is None else req.full_name.strip()

        password_hash = user["password_hash"]
        must_change = user.get("must_change_password") or 0
        if req.new_password:
            _validate_password(req.new_password)
            password_hash = hash_password(req.new_password)
            must_change = 1  # staff member should pick their own password next time

        conn.execute(
            "UPDATE users SET username = ?, full_name = ?, password_hash = ?, must_change_password = ? WHERE id = ?",
            (username, full_name, password_hash, must_change, user_id),
        )
        updated = dict(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())
    return {"success": True, "user": public_user(updated)}
