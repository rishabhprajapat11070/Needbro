from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import date, time, datetime
from decimal import Decimal


# ─── Auth ─────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ─── User ─────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    mobile: str
    password: str
    referral_code: Optional[str] = None

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    mobile: str
    photo: Optional[str]
    wallet_balance: Decimal
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str]
    photo: Optional[str]
    mobile: Optional[str]


# ─── Provider ─────────────────────────────────────────────────────────────────

class ProviderRegister(BaseModel):
    name: str
    email: EmailStr
    mobile: str
    password: str
    experience_years: Optional[int] = 0
    bio: Optional[str]
    shop_address: Optional[str]
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    upi_id: Optional[str]

class ProviderOut(BaseModel):
    id: int
    name: str
    email: str
    mobile: str
    photo: Optional[str]
    experience_years: int
    bio: Optional[str]
    shop_address: Optional[str]
    is_verified: bool
    availability_status: str
    avg_rating: Decimal
    total_jobs: int
    created_at: datetime
    class Config:
        from_attributes = True

class ProviderUpdate(BaseModel):
    name: Optional[str]
    bio: Optional[str]
    shop_address: Optional[str]
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    upi_id: Optional[str]
    availability_status: Optional[str]


# ─── Category ─────────────────────────────────────────────────────────────────

class CategoryOut(BaseModel):
    id: int
    name: str
    icon: Optional[str]
    is_active: bool
    class Config:
        from_attributes = True

class CategoryCreate(BaseModel):
    name: str
    icon: Optional[str]


# ─── Service ──────────────────────────────────────────────────────────────────

class ServiceOut(BaseModel):
    id: int
    category_id: int
    name: str
    description: Optional[str]
    base_price: Optional[Decimal]
    class Config:
        from_attributes = True

class ServiceCreate(BaseModel):
    category_id: int
    name: str
    description: Optional[str]
    base_price: Optional[Decimal]


# ─── Booking ──────────────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    provider_id: int
    service_id: int
    booking_date: date
    booking_time: time
    address: str
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    problem_description: Optional[str]
    is_emergency: bool = False
    coupon_code: Optional[str]

class BookingOut(BaseModel):
    id: int
    user_id: int
    provider_id: int
    service_id: int
    booking_date: date
    booking_time: time
    address: str
    problem_description: Optional[str]
    status: str
    is_emergency: bool
    base_amount: Optional[Decimal]
    discount_amount: Optional[Decimal]
    final_amount: Optional[Decimal]
    created_at: datetime
    class Config:
        from_attributes = True

class BookingStatusUpdate(BaseModel):
    status: str
    note: Optional[str]


# ─── Payment ──────────────────────────────────────────────────────────────────

class PaymentCreate(BaseModel):
    booking_id: int
    payment_method: str

class PaymentOut(BaseModel):
    id: int
    booking_id: int
    amount: Decimal
    payment_method: str
    payment_status: str
    transaction_id: Optional[str]
    paid_at: Optional[datetime]
    class Config:
        from_attributes = True


# ─── Review ───────────────────────────────────────────────────────────────────

class ReviewCreate(BaseModel):
    booking_id: int
    rating: int
    comment: Optional[str]

    @validator("rating")
    def rating_range(cls, v):
        if not 1 <= v <= 5:
            raise ValueError("Rating must be 1–5")
        return v

class ReviewOut(BaseModel):
    id: int
    booking_id: int
    user_id: int
    provider_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


# ─── Chat ─────────────────────────────────────────────────────────────────────

class ChatMessageOut(BaseModel):
    id: int
    booking_id: int
    sender_type: str
    sender_id: int
    message_type: str
    content: str
    is_read: bool
    sent_at: datetime
    class Config:
        from_attributes = True


# ─── Complaint ────────────────────────────────────────────────────────────────

class ComplaintCreate(BaseModel):
    booking_id: int
    type: str
    description: Optional[str]

class ComplaintOut(BaseModel):
    id: int
    booking_id: int
    raised_by: str
    type: str
    description: Optional[str]
    status: str
    created_at: datetime
    class Config:
        from_attributes = True


# ─── Notification ─────────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: int
    title: str
    body: Optional[str]
    is_read: bool
    created_at: datetime
    class Config:
        from_attributes = True


# ─── Search ───────────────────────────────────────────────────────────────────

class SearchFilters(BaseModel):
    query: Optional[str]
    category_id: Optional[int]
    min_price: Optional[Decimal]
    max_price: Optional[Decimal]
    min_rating: Optional[float]
    max_distance_km: Optional[float]
    user_lat: Optional[Decimal]
    user_lng: Optional[Decimal]
    available_today: Optional[bool]
    verified_only: Optional[bool]


# ─── Coupon ───────────────────────────────────────────────────────────────────

class CouponValidate(BaseModel):
    code: str
    order_amount: Decimal

class CouponOut(BaseModel):
    id: int
    code: str
    discount_type: str
    discount_value: Decimal
    class Config:
        from_attributes = True
