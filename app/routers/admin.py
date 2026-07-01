from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.connection import get_db
from app.models.models import (
    Admin, User, Provider, ProviderDocument, Booking,
    Payment, Review, Complaint, Category, Coupon, Notification
)
from app.schemas.schemas import Token, LoginRequest, CategoryCreate, CouponOut
from app.auth.security import verify_password, create_access_token, get_current_admin, hash_password
from pydantic import BaseModel, EmailStr
from datetime import date, timedelta

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ─── Admin Auth ───────────────────────────────────────────────────────────────

@router.post("/login", response_model=Token)
def admin_login(data: LoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == data.email).first()
    if not admin or not verify_password(data.password, admin.password):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"sub": admin.id, "role": "admin"})
    return {"access_token": token}


# ─── Dashboard ────────────────────────────────────────────────────────────────

@router.get("/dashboard")
def admin_dashboard(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    today = date.today()
    week_ago = today - timedelta(days=7)

    total_users     = db.query(func.count(User.id)).scalar()
    total_providers = db.query(func.count(Provider.id)).scalar()
    total_bookings  = db.query(func.count(Booking.id)).scalar()
    pending_bookings = db.query(func.count(Booking.id)).filter(Booking.status == "pending").scalar()
    total_revenue   = db.query(func.sum(Payment.amount)).filter(
        Payment.payment_status == "success"
    ).scalar() or 0
    week_revenue    = db.query(func.sum(Payment.amount)).filter(
        Payment.payment_status == "success",
        Payment.paid_at >= week_ago
    ).scalar() or 0
    pending_verifications = db.query(func.count(Provider.id)).filter(
        Provider.is_verified == False
    ).scalar()
    open_complaints = db.query(func.count(Complaint.id)).filter(
        Complaint.status == "open"
    ).scalar()

    return {
        "total_users": total_users,
        "total_providers": total_providers,
        "total_bookings": total_bookings,
        "pending_bookings": pending_bookings,
        "total_revenue": float(total_revenue),
        "week_revenue": float(week_revenue),
        "pending_verifications": pending_verifications,
        "open_complaints": open_complaints,
    }


# ─── Users ────────────────────────────────────────────────────────────────────

@router.get("/users")
def list_users(page: int = 1, limit: int = 20, db: Session = Depends(get_db),
               _=Depends(get_current_admin)):
    skip = (page - 1) * limit
    users = db.query(User).offset(skip).limit(limit).all()
    return [{"id": u.id, "name": u.name, "email": u.email,
             "mobile": u.mobile, "is_active": u.is_active,
             "created_at": u.created_at} for u in users]


@router.put("/users/{user_id}/toggle-active")
def toggle_user(user_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.is_active = not user.is_active
    db.commit()
    return {"is_active": user.is_active}


# ─── Providers ────────────────────────────────────────────────────────────────

@router.get("/providers")
def list_providers(verified: bool = None, db: Session = Depends(get_db),
                   _=Depends(get_current_admin)):
    q = db.query(Provider)
    if verified is not None:
        q = q.filter(Provider.is_verified == verified)
    providers = q.all()
    return [{"id": p.id, "name": p.name, "email": p.email,
             "is_verified": p.is_verified, "is_active": p.is_active,
             "avg_rating": float(p.avg_rating), "total_jobs": p.total_jobs}
            for p in providers]


@router.put("/providers/{provider_id}/verify")
def verify_provider(provider_id: int, db: Session = Depends(get_db),
                    _=Depends(get_current_admin)):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(404, "Provider not found")
    provider.is_verified = True
    # Approve all their documents
    for doc in provider.documents:
        doc.is_approved = True
    # Notify provider
    db.add(Notification(
        provider_id=provider_id,
        title="Account Verified!",
        body="Congratulations! Your NeedBro account is now verified. You can start accepting jobs.",
    ))
    db.commit()
    return {"message": "Provider verified", "provider_id": provider_id}


@router.put("/providers/{provider_id}/toggle-active")
def toggle_provider(provider_id: int, db: Session = Depends(get_db),
                    _=Depends(get_current_admin)):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(404, "Provider not found")
    provider.is_active = not provider.is_active
    db.commit()
    return {"is_active": provider.is_active}


# ─── Bookings ─────────────────────────────────────────────────────────────────

@router.get("/booking")
def admin_bookings(status: str = None, page: int = 1, limit: int = 20,
                   db: Session = Depends(get_db), _=Depends(get_current_admin)):
    q = db.query(Booking)
    if status:
        q = q.filter(Booking.status == status)
    skip = (page - 1) * limit
    bookings = q.order_by(Booking.created_at.desc()).offset(skip).limit(limit).all()
    return [{"id": b.id, "user_id": b.user_id, "provider_id": b.provider_id,
             "status": b.status, "final_amount": float(b.final_amount or 0),
             "booking_date": b.booking_date, "created_at": b.created_at}
            for b in bookings]


# ─── Complaints ───────────────────────────────────────────────────────────────

@router.get("/complaints")
def admin_complaints(status: str = "open", db: Session = Depends(get_db),
                     _=Depends(get_current_admin)):
    complaints = db.query(Complaint).filter(Complaint.status == status).all()
    return [{"id": c.id, "booking_id": c.booking_id, "type": c.type,
             "raised_by": c.raised_by, "description": c.description,
             "status": c.status, "created_at": c.created_at} for c in complaints]


@router.put("/complaints/{complaint_id}/resolve")
def resolve_complaint(complaint_id: int, db: Session = Depends(get_db),
                      _=Depends(get_current_admin)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(404, "Complaint not found")
    complaint.status = "resolved"
    db.commit()
    return {"message": "Complaint resolved"}


# ─── Categories ───────────────────────────────────────────────────────────────

@router.post("/categories")
def create_category(data: CategoryCreate, db: Session = Depends(get_db),
                    _=Depends(get_current_admin)):
    cat = Category(name=data.name, icon=data.icon)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


# ─── Coupons ──────────────────────────────────────────────────────────────────

class CouponCreate(BaseModel):
    code: str
    discount_type: str
    discount_value: float
    min_order: float = 0
    max_uses: int = 100
    valid_until: date

@router.post("/coupons")
def create_coupon(data: CouponCreate, db: Session = Depends(get_db),
                  _=Depends(get_current_admin)):
    coupon = Coupon(**data.dict())
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.get("/coupons")
def list_coupons(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return db.query(Coupon).all()


# ─── Reviews ──────────────────────────────────────────────────────────────────

@router.put("/reviews/{review_id}/flag")
def flag_review(review_id: int, db: Session = Depends(get_db),
                _=Depends(get_current_admin)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(404, "Review not found")
    review.is_flagged = not review.is_flagged
    db.commit()
    return {"is_flagged": review.is_flagged}
