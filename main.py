from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os

load_dotenv()

# Import routers
from app.routers.auth import router as auth_router
from app.routers.provider import router as provider_router
from app.routers.search   import router as search_router
from app.routers.bookings import router as bookings_router
from app.routers.payments import router as payments_router
from app.routers.admin    import router as admin_router
from app.websocket.chat   import router as chat_router

# Create tables on startup
from app.database.connection import engine
from app.models import models
models.Base.metadata.create_all(bind=engine)

# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="NeedBro API",
    description="Home Services Marketplace — Connect customers with local professionals",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static files ─────────────────────────────────────────────────────────────

os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(provider_router)
app.include_router(search_router)
app.include_router(bookings_router)
app.include_router(payments_router)
app.include_router(admin_router)
app.include_router(chat_router)

# ─── Root ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return FileResponse("templates/index.html")


@app.get("/admin")
def admin():
    return FileResponse("templates/admin.html")


@app.get("/booking")
def booking():
    return FileResponse("templates/booking.html")


@app.get("/booking-detail")
def booking_detail():
    return FileResponse("templates/booking-detail.html")


@app.get("/chat")
def chat():
    return FileResponse("templates/chat.html")


@app.get("/dashboard")
def dashboard():
    return FileResponse("templates/dashboard.html")


@app.get("/favorites")
def favorites():
    return FileResponse("templates/favorites.html")


@app.get("/profile")
def profile():
    return FileResponse("templates/profile.html")


@app.get("/provider-bookings")
def provider_bookings():
    return FileResponse("templates/provider-bookings.html")


@app.get("/provider-dashboard")
def provider_dashboard():
    return FileResponse("templates/provider-dashboard.html")


@app.get("/provider-documents")
def provider_documents():
    return FileResponse("templates/provider-documents.html")


@app.get("/provider-earnings")
def provider_earnings():
    return FileResponse("templates/provider-earnings.html")


@app.get("/provider-login")
def provider_login():
    return FileResponse("templates/provider-login.html")


@app.get("/provider-profile")
def provider_profile():
    return FileResponse("templates/provider-profile.html")


@app.get("/provider-register")
def provider_register():
    return FileResponse("templates/provider-register.html")


@app.get("/provider")
def provider():
    return FileResponse("templates/provider.html")


@app.get("/search")
def search():
    return FileResponse("templates/search.html")


@app.get("/track")
def track():
    return FileResponse("templates/track.html")


@app.get("/health")
def health():
    return {"status": "ok", "app": "NeedBro"}




