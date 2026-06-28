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

@app.get("/health")
def health():
    return {"status": "ok", "app": "NeedBro"}
