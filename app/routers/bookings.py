from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import (
    Booking, BookingStatusLog, Service, Coupon, Notification,
    Provider, User
)
from app.schemas.schemas import BookingCreate, BookingOut, BookingStatusUpdate
from needbro.app.routers.auth import get_current_user
from app.utils.helpers import save_upload
from datetime import date

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])


@router.post("", response_model=BookingOut)
async def create_booking(data: BookingCreate, db: Session = Depends(get_db),
                          user: User = Depends(get_current_user)):
    service = db.query(Service).filter(Service.id == data.service_id).first()
    if not service:
        raise HTTPException(404, "Service not found")

    provider = db.query(Provider).filter(Provider.id == data.provider_id).first()
    if not provider:
        raise HTTPException(404, "Provider not found")
    if not provider.is_verified:
        raise HTTPException(400, "Provider is not yet verified")

    base_amount = float(service.base_price or 0)
    if data.is_emergency:
        base_amount *= 1.5  # 50% emergency surcharge

    discount = 0
    coupon_id = None
    if data.coupon_code:
        coupon = db.query(Coupon).filter(
            Coupon.code == data.coupon_code,
            Coupon.is_active == True
        ).first()
        if coupon and coupon.used_count < coupon.max_uses:
            if base_amount >= float(coupon.min_order):
                if coupon.discount_type == "flat":
                    discount = float(coupon.discount_value)
                else:
                    discount = base_amount * float(coupon.discount_value) / 100
                coupon.used_count += 1
                coupon_id = coupon.id

    final = max(base_amount - discount, 0)

    booking = Booking(
        user_id=user.id,
        provider_id=data.provider_id,
        service_id=data.service_id,
        booking_date=data.booking_date,
        booking_time=data.booking_time,
        address=data.address,
        latitude=data.latitude,
        longitude=data.longitude,
        problem_description=data.problem_description,
        is_emergency=data.is_emergency,
        coupon_id=coupon_id,
        base_amount=base_amount,
        discount_amount=discount,
        final_amount=final,
        status="pending",
    )
    db.add(booking)
    db.flush()

    # Status log
    db.add(BookingStatusLog(booking_id=booking.id, status="pending"))

    # Notify provider
    db.add(Notification(
        provider_id=data.provider_id,
        title="New Booking Request",
        body=f"{user.name} needs {service.name} on {data.booking_date}",
    ))

    db.commit()
    db.refresh(booking)
    return booking


@router.get("", response_model=list[BookingOut])
def list_user_bookings(status: str = None, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    q = db.query(Booking).filter(Booking.user_id == user.id)
    if status:
        q = q.filter(Booking.status == status)
    return q.order_by(Booking.created_at.desc()).all()


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == user.id
    ).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    return booking


@router.put("/{booking_id}/cancel")
def cancel_booking(booking_id: int, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == user.id
    ).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    if booking.status not in ["pending", "accepted"]:
        raise HTTPException(400, "Cannot cancel a booking that is already in progress")

    booking.status = "cancelled"
    db.add(BookingStatusLog(booking_id=booking.id, status="cancelled"))
    db.commit()
    return {"message": "Booking cancelled"}


@router.get("/{booking_id}/status-log")
def booking_status_log(booking_id: int, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == user.id
    ).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    return [{"status": s.status, "changed_at": s.changed_at, "note": s.note}
            for s in booking.status_logs]


@router.post("/{booking_id}/problem-image")
async def upload_problem_image(booking_id: int, file: UploadFile = File(...),
                                db: Session = Depends(get_db),
                                user: User = Depends(get_current_user)):
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == user.id
    ).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    path = await save_upload(file, folder="problems")
    booking.problem_image = path
    db.commit()
    return {"problem_image": path}
