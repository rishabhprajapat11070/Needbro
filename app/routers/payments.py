from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.connection import get_db
from app.models.models import (
    Payment, Booking, Review, Provider, Notification,
    Favorite, Complaint, Coupon, User, Transaction
)
from app.schemas.schemas import (
    PaymentCreate, PaymentOut, ReviewCreate, ReviewOut,
    ComplaintCreate, ComplaintOut, NotificationOut, CouponValidate
)
from needbro.app.routers.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api", tags=["Payments & Reviews"])


# ─── Payments ─────────────────────────────────────────────────────────────────

@router.post("/payments", response_model=PaymentOut)
def create_payment(data: PaymentCreate, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    booking = db.query(Booking).filter(
        Booking.id == data.booking_id,
        Booking.user_id == user.id
    ).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    if booking.status != "completed":
        raise HTTPException(400, "Payment only allowed after service is completed")

    existing = db.query(Payment).filter(Payment.booking_id == data.booking_id).first()
    if existing and existing.payment_status == "success":
        raise HTTPException(400, "Already paid")

    payment = Payment(
        booking_id=data.booking_id,
        amount=booking.final_amount,
        payment_method=data.payment_method,
        payment_status="success",  # For cash; Razorpay webhook sets this for UPI/card
        paid_at=datetime.utcnow(),
    )
    db.add(payment)

    # Credit provider wallet (80% after platform cut)
    provider = db.query(Provider).filter(Provider.id == booking.provider_id).first()
    if provider:
        earnings = float(booking.final_amount) * 0.80
        provider.wallet_balance += earnings
        db.add(Transaction(
            provider_id=provider.id,
            booking_id=booking.id,
            amount=earnings,
            type="credit",
            description=f"Earnings from booking #{booking.id}"
        ))
        db.add(Notification(
            provider_id=provider.id,
            title="Payment Received",
            body=f"₹{earnings:.0f} credited for booking #{booking.id}"
        ))

    db.add(Notification(
        user_id=user.id,
        title="Payment Successful",
        body=f"₹{booking.final_amount} paid for booking #{booking.id}"
    ))

    db.commit()
    db.refresh(payment)
    return payment


@router.get("/payments/{booking_id}", response_model=PaymentOut)
def get_payment(booking_id: int, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == user.id
    ).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()
    if not payment:
        raise HTTPException(404, "Payment not found")
    return payment


# ─── Reviews ──────────────────────────────────────────────────────────────────

@router.post("/reviews", response_model=ReviewOut)
def create_review(data: ReviewCreate, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    booking = db.query(Booking).filter(
        Booking.id == data.booking_id,
        Booking.user_id == user.id,
        Booking.status == "completed"
    ).first()
    if not booking:
        raise HTTPException(404, "Completed booking not found")

    existing = db.query(Review).filter(Review.booking_id == data.booking_id).first()
    if existing:
        raise HTTPException(400, "Already reviewed")

    review = Review(
        booking_id=data.booking_id,
        user_id=user.id,
        provider_id=booking.provider_id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    db.flush()

    # Update provider avg rating
    provider = db.query(Provider).filter(Provider.id == booking.provider_id).first()
    if provider:
        avg = db.query(func.avg(Review.rating)).filter(
            Review.provider_id == provider.id
        ).scalar()
        provider.avg_rating = round(float(avg), 2)

    db.commit()
    db.refresh(review)
    return review


@router.get("/providers/{provider_id}/reviews", response_model=list[ReviewOut])
def provider_reviews(provider_id: int, db: Session = Depends(get_db)):
    return db.query(Review).filter(Review.provider_id == provider_id).order_by(
        Review.created_at.desc()
    ).limit(50).all()


# ─── Notifications ────────────────────────────────────────────────────────────

@router.get("/notifications", response_model=list[NotificationOut])
def get_notifications(db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    return db.query(Notification).filter(
        Notification.user_id == user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()


@router.put("/notifications/{notif_id}/read")
def mark_read(notif_id: int, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    n = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == user.id
    ).first()
    if n:
        n.is_read = True
        db.commit()
    return {"message": "Marked as read"}


# ─── Favorites ────────────────────────────────────────────────────────────────

@router.post("/favorites/{provider_id}")
def add_favorite(provider_id: int, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    if not db.query(Provider).filter(Provider.id == provider_id).first():
        raise HTTPException(404, "Provider not found")
    existing = db.query(Favorite).filter(
        Favorite.user_id == user.id,
        Favorite.provider_id == provider_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"message": "Removed from favorites"}
    db.add(Favorite(user_id=user.id, provider_id=provider_id))
    db.commit()
    return {"message": "Added to favorites"}


@router.get("/favorites")
def get_favorites(db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    favs = db.query(Favorite).filter(Favorite.user_id == user.id).all()
    return [{"provider_id": f.provider_id, "name": f.provider.name,
             "photo": f.provider.photo, "avg_rating": float(f.provider.avg_rating)}
            for f in favs]


# ─── Complaints ───────────────────────────────────────────────────────────────

@router.post("/complaints", response_model=ComplaintOut)
def create_complaint(data: ComplaintCreate, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    booking = db.query(Booking).filter(
        Booking.id == data.booking_id,
        Booking.user_id == user.id
    ).first()
    if not booking:
        raise HTTPException(404, "Booking not found")

    complaint = Complaint(
        booking_id=data.booking_id,
        raised_by="user",
        raised_by_id=user.id,
        type=data.type,
        description=data.description,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


# ─── Coupons ──────────────────────────────────────────────────────────────────

@router.post("/coupons/validate")
def validate_coupon(data: CouponValidate, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    coupon = db.query(Coupon).filter(
        Coupon.code == data.code,
        Coupon.is_active == True
    ).first()
    if not coupon:
        raise HTTPException(404, "Invalid coupon code")
    if coupon.used_count >= coupon.max_uses:
        raise HTTPException(400, "Coupon has expired")
    if float(data.order_amount) < float(coupon.min_order):
        raise HTTPException(400, f"Minimum order ₹{coupon.min_order} required")

    if coupon.discount_type == "flat":
        discount = float(coupon.discount_value)
    else:
        discount = float(data.order_amount) * float(coupon.discount_value) / 100

    return {
        "code": coupon.code,
        "discount_type": coupon.discount_type,
        "discount_value": float(coupon.discount_value),
        "discount_amount": round(discount, 2),
        "final_amount": round(float(data.order_amount) - discount, 2),
    }
