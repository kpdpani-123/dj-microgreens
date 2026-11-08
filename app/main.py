import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.database import init_db, get_db
from app.seed_data import seed_database
from app.auth import (
    SESSION_COOKIE,
    ensure_staff_accounts,
    get_user_from_token,
    required_tabs_for_path,
    ROLE_TABS,
)
from app.routers import api, admin, exports, auth

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="DJ Microgreens – Chennai E-commerce & Farm Management Platform",
    description="Freshness Delivered. Nutrition Naturally. Production-ready microgreens platform with customer mobile app and farm business operations.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files & templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Include API Routers
app.include_router(api.router)
app.include_router(admin.router)
app.include_router(exports.router)
app.include_router(auth.router)

_db_ready = False

def prepare_database():
    global _db_ready
    if _db_ready:
        return
    init_db()
    seed_database()
    ensure_staff_accounts()
    _db_ready = True

@app.on_event("startup")
def on_startup():
    prepare_database()

@app.middleware("http")
async def staff_login_guard(request: Request, call_next):
    prepare_database()
    tabs = required_tabs_for_path(request.url.path)
    if tabs is not None:
        user = get_user_from_token(request.cookies.get(SESSION_COOKIE))
        if not user:
            return JSONResponse({"detail": "Please sign in"}, status_code=401)
        if not set(tabs) & set(ROLE_TABS.get(user["role"], [])):
            return JSONResponse({"detail": "Your role does not have access to this section"}, status_code=403)
        request.state.user = user
    return await call_next(request)

@app.get("/", response_class=HTMLResponse)
async def customer_home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})

@app.get("/login", response_class=HTMLResponse)
async def staff_login_page(request: Request):
    if get_user_from_token(request.cookies.get(SESSION_COOKIE)):
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={})

@app.get("/admin", response_class=HTMLResponse)
async def admin_portal(request: Request):
    if not get_user_from_token(request.cookies.get(SESSION_COOKIE)):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request=request, name="admin.html", context={})

@app.get("/b2b", response_class=HTMLResponse)
async def b2b_portal(request: Request):
    return templates.TemplateResponse(request=request, name="b2b.html", context={})

@app.get("/invoice/{order_number}", response_class=HTMLResponse)
async def view_invoice(request: Request, order_number: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE order_number = ?", (order_number.strip(),))
        order = cursor.fetchone()
        if not order:
            return HTMLResponse("<h3>Order not found</h3>", status_code=404)
        
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],))
        items = [dict(r) for r in cursor.fetchall()]

        return templates.TemplateResponse(
            request=request,
            name="invoice.html",
            context={
                "order": dict(order),
                "items": items
            }
        )

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": "DJ Microgreens",
        "city": "Chennai, Tamil Nadu",
        "version": "1.0.0"
    }
