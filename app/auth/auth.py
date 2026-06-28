from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import User, Provider, Admin
import os

SECRET_KEY = os.getenv("SECRET_KEY", "changeme_secret_key_32chars_minimum")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")
EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 10080))

pwd_context       = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme     = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
provider_scheme   = OAuth2PasswordBearer(tokenUrl="/api/provider/auth/login")
admin_scheme      = OAuth2PasswordBearer(tokenUrl="/api/admin/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=EXPIRE_MIN))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Dependency: current customer ──────────────────────────────────────────────
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    if payload.get("role") != "user":
        raise HTTPException(status_code=403, detail="Not a customer token")
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ── Dependency: current provider ──────────────────────────────────────────────
def get_current_provider(token: str = Depends(provider_scheme), db: Session = Depends(get_db)) -> Provider:
    payload = decode_token(token)
    if payload.get("role") != "provider":
        raise HTTPException(status_code=403, detail="Not a provider token")
    provider = db.query(Provider).filter(Provider.id == payload.get("sub")).first()
    if not provider or not provider.is_active:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


# ── Dependency: current admin ─────────────────────────────────────────────────
def get_current_admin(token: str = Depends(admin_scheme), db: Session = Depends(get_db)) -> Admin:
    payload = decode_token(token)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not an admin token")
    admin = db.query(Admin).filter(Admin.id == payload.get("sub")).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin
