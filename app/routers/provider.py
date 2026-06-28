from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.connection import get_db
from app.models.models import Provider, ProviderDocument, ProviderSkill, Booking, BookingStatus
from app.schemas.schemas import (
    ProviderRegister, ProviderOut, ProviderUpdate,
    Token, LoginRequest, BookingOut, BookingStatusUpdate
)
from app.auth.security import hash_password, verify_password, create_access_token, get_current_provider
from app.utils.helpers import save_upload

router = APIRouter(prefix="/api/provider", tags=["Provider"])


@router.post("/auth/register", response_model=Token)
def provider_register(data: ProviderRegister, db: Session = Depends(get_db)):
    if db.query(Provider).filter(Provider.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    if db.query(Provider).filter(Provider.mobile == data.mobile).first():
        raise HTTPException(400, "Mobile already registered")

    provider = Provider(
        name=data.name,
        email=data.email,
        mobile=data.mobile,
        password=hash_password(data.password),
        experience_years=data.experience_years,
        bio=data.bio,
        shop_address=data.shop_address,
        latitude=data.latitude,
        longitude=data.longitude,
        upi_id=data.upi_id,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    token = create_access_token({"sub": provider.id, "role": "provider"})
    return {"access_token": token}


@router.post("/auth/login", response_model=Token)
def provider_login(data: LoginRequest, db: Session = Depends(get_db)):
    provider = db.query(Provider).filter(Provider.email == data.email).first()
    if not provider or not verify_password(data.password, provider.password):
        raise HTTPException(401, "Invalid email or password")
    if not provider.is_active:
        raise HTTPException(403, "Account is deactivated")
    token = create_access_token({"sub": provider.id, "role": "provider"})
    return {"access_token": token}


@router.get("/me", response_model=ProviderOut)
def get_provider_profile(provider: Provider = Depends(get_current_provider)):
    return provider


@router.put("/profile", response_model=ProviderOut)
def update_provider_profile(data: ProviderUpdate, db: Session = Depends(get_db),
                             provider: Provider = Depends(get_current_provider)):
    for field, val in data.dict(exclude_unset=True).items():
        setattr(provider, field, val)
    db.commit()
    db.refresh(provider)
    return provider


@router.post("/profile/photo")
async def upload_provider_photo(file: UploadFile = File(...), db: Session = Depends(get_db),
                                 provider: Provider = Depends(get_current_provider)):
    path = await save_upload(file, folder="providers")
    provider.photo = path
    db.commit()
    return {"photo": path}


@router.post("/documents")
async def upload_document(
    doc_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider)
):
    if doc_type not in ["aadhaar", "pan", "certificate", "other"]:
        raise HTTPException(400, "Invalid document type")
    path = await save_upload(file, folder="documents")
    doc = ProviderDocument(provider_id=provider.id, doc_type=doc_type, file_path=path)
    db.add(doc)
    db.commit()
    return {"message": "Document uploaded, pending admin approval", "file": path}


@router.get("/dashboard")
def provider_dashboard(db: Session = Depends(get_db),
                       provider: Provider = Depends(get_current_provider)):
    from datetime import date
    today = date.today()

    today_bookings = db.query(Booking).filter(
        Booking.provider_id == provider.id,
        Booking.booking_date == today
    ).count()

    pending = db.query(Booking).filter(
        Booking.provider_id == provider.id,
        Booking.status == "pending"
    ).count()

    completed = db.query(Booking).filter(
        Booking.provider_id == provider.id,
        Booking.status == "completed"
    ).count()

    return {
        "name": provider.name,
        "avg_rating": float(provider.avg_rating),
        "total_jobs": provider.total_jobs,
        "wallet_balance": float(provider.wallet_balance),
        "availability_status": provider.availability_status,
        "today_bookings": today_bookings,
        "pending_bookings": pending,
        "completed_bookings": completed,
    }


@router.get("/bookings", response_model=list[BookingOut])
def provider_bookings(status: str = None, db: Session = Depends(get_db),
                      provider: Provider = Depends(get_current_provider)):
    q = db.query(Booking).filter(Booking.provider_id == provider.id)
    if status:
        q = q.filter(Booking.status == status)
    return q.order_by(Booking.created_at.desc()).all()


@router.put("/bookings/{booking_id}/status")
def update_booking_status(booking_id: int, data: BookingStatusUpdate,
                           db: Session = Depends(get_db),
                           provider: Provider = Depends(get_current_provider)):
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.provider_id == provider.id
    ).first()
    if not booking:
        raise HTTPException(404, "Booking not found")

    booking.status = data.status
    log = BookingStatus(booking_id=booking_id, status=data.status, note=data.note)
    db.add(log)

    # Update provider stats on completion
    if data.status == "completed":
        provider.total_jobs += 1

    db.commit()
    return {"message": f"Booking status updated to {data.status}"}


@router.get("/earnings")
def provider_earnings(db: Session = Depends(get_db),
                      provider: Provider = Depends(get_current_provider)):
    from datetime import date, timedelta
    today = date.today()
    week_start = today - timedelta(days=7)
    month_start = today.replace(day=1)

    def sum_completed(from_date):
        result = db.query(func.sum(Booking.final_amount)).filter(
            Booking.provider_id == provider.id,
            Booking.status == "completed",
            Booking.booking_date >= from_date
        ).scalar()
        return float(result or 0)

    return {
        "wallet_balance": float(provider.wallet_balance),
        "today": sum_completed(today),
        "weekly": sum_completed(week_start),
        "monthly": sum_completed(month_start),
    }


@router.put("/availability")
def set_availability(status: str, db: Session = Depends(get_db),
                     provider: Provider = Depends(get_current_provider)):
    valid = ["online", "offline", "busy", "vacation"]
    if status not in valid:
        raise HTTPException(400, f"Status must be one of {valid}")
    provider.availability_status = status
    db.commit()
    return {"availability_status": status}
