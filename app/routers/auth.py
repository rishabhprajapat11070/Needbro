from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import User
from app.schemas.schemas import UserRegister, UserOut, UserUpdate, Token, LoginRequest
from needbro.app.routers.auth import hash_password, verify_password, create_access_token, get_current_user
from app.utils.helpers import save_upload, generate_referral_code
import random, string

router = APIRouter(prefix="/api/auth", tags=["Customer Auth"])


@router.post("/register", response_model=Token)
def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    if db.query(User).filter(User.mobile == data.mobile).first():
        raise HTTPException(400, "Mobile already registered")

    referred_by_id = None
    if data.referral_code:
        ref_user = db.query(User).filter(User.referral_code == data.referral_code).first()
        if ref_user:
            referred_by_id = ref_user.id
            ref_user.wallet_balance += 50  # ₹50 referral bonus

    user = User(
        name=data.name,
        email=data.email,
        mobile=data.mobile,
        password=hash_password(data.password),
        referral_code=generate_referral_code(),
        referred_by=referred_by_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "role": "user"})
    return {"access_token": token}


@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account is deactivated")
    token = create_access_token({"sub": user.id, "role": "user"})
    return {"access_token": token}


@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserOut)
def update_profile(data: UserUpdate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    for field, val in data.dict(exclude_unset=True).items():
        setattr(current_user, field, val)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/profile/photo", response_model=UserOut)
async def upload_photo(file: UploadFile = File(...), db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    path = await save_upload(file, folder="users")
    current_user.photo = path
    db.commit()
    db.refresh(current_user)
    return current_user
