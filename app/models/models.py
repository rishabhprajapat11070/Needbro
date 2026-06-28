from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, Time,
    Enum, DECIMAL, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
import enum


# ─── Enums ────────────────────────────────────────────────────────────────────

class AvailabilityStatus(str, enum.Enum):
    online   = "online"
    offline  = "offline"
    busy     = "busy"
    vacation = "vacation"

class BookingStatus(str, enum.Enum):
    pending   = "pending"
    accepted  = "accepted"
    rejected  = "rejected"
    coming    = "coming"
    reached   = "reached"
    working   = "working"
    completed = "completed"
    cancelled = "cancelled"

class PaymentMethod(str, enum.Enum):
    cash   = "cash"
    upi    = "upi"
    card   = "card"
    wallet = "wallet"

class PaymentStatus(str, enum.Enum):
    pending  = "pending"
    success  = "success"
    failed   = "failed"
    refunded = "refunded"

class ComplaintType(str, enum.Enum):
    late_arrival = "late_arrival"
    fraud        = "fraud"
    bad_work     = "bad_work"
    overcharging = "overcharging"
    other        = "other"

class ComplaintStatus(str, enum.Enum):
    open      = "open"
    in_review = "in_review"
    resolved  = "resolved"
    closed    = "closed"

class MessageType(str, enum.Enum):
    text     = "text"
    image    = "image"
    location = "location"


# ─── Models ───────────────────────────────────────────────────────────────────

class Admin(Base):
    __tablename__ = "admin"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, nullable=False)
    password   = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())


class User(Base):
    __tablename__ = "users"
    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String(100), nullable=False)
    email          = Column(String(150), unique=True, nullable=False)
    mobile         = Column(String(15), unique=True, nullable=False)
    password       = Column(String(255), nullable=False)
    photo          = Column(String(255))
    referral_code  = Column(String(20), unique=True)
    referred_by    = Column(Integer, ForeignKey("users.id"), nullable=True)
    wallet_balance = Column(DECIMAL(10, 2), default=0.00)
    is_active      = Column(Boolean, default=True)
    created_at     = Column(DateTime, default=func.now())

    bookings       = relationship("Booking", back_populates="user")
    locations      = relationship("UserLocation", back_populates="user")
    reviews        = relationship("Review", back_populates="user")
    favorites      = relationship("Favorite", back_populates="user")
    notifications  = relationship("Notification", back_populates="user")


class Category(Base):
    __tablename__ = "categories"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    icon       = Column(String(255))
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    services   = relationship("Service", back_populates="category")


class Service(Base):
    __tablename__ = "services"
    id          = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    name        = Column(String(150), nullable=False)
    description = Column(Text)
    base_price  = Column(DECIMAL(10, 2))
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=func.now())

    category    = relationship("Category", back_populates="services")
    bookings    = relationship("Booking", back_populates="service")


class Provider(Base):
    __tablename__ = "providers"
    id                  = Column(Integer, primary_key=True, index=True)
    name                = Column(String(100), nullable=False)
    email               = Column(String(150), unique=True, nullable=False)
    mobile              = Column(String(15), unique=True, nullable=False)
    password            = Column(String(255), nullable=False)
    photo               = Column(String(255))
    aadhaar_number      = Column(String(20))
    pan_number          = Column(String(20))
    experience_years    = Column(Integer, default=0)
    bio                 = Column(Text)
    shop_address        = Column(Text)
    latitude            = Column(DECIMAL(10, 8))
    longitude           = Column(DECIMAL(11, 8))
    bank_account        = Column(String(30))
    upi_id              = Column(String(100))
    is_verified         = Column(Boolean, default=False)
    is_active           = Column(Boolean, default=True)
    availability_status = Column(Enum(AvailabilityStatus), default=AvailabilityStatus.offline)
    avg_rating          = Column(DECIMAL(3, 2), default=0.00)
    total_jobs          = Column(Integer, default=0)
    wallet_balance      = Column(DECIMAL(10, 2), default=0.00)
    created_at          = Column(DateTime, default=func.now())

    documents           = relationship("ProviderDocument", back_populates="provider")
    skills              = relationship("ProviderSkill", back_populates="provider")
    availability        = relationship("ProviderAvailability", back_populates="provider")
    bookings            = relationship("Booking", back_populates="provider")
    reviews             = relationship("Review", back_populates="provider")
    notifications       = relationship("Notification", back_populates="provider")
    transactions        = relationship("Transaction", back_populates="provider")


class ProviderDocument(Base):
    __tablename__ = "provider_documents"
    id          = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    doc_type    = Column(Enum("aadhaar", "pan", "certificate", "other", name="doc_type_enum"), nullable=False)
    file_path   = Column(String(255), nullable=False)
    is_approved = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, default=func.now())

    provider    = relationship("Provider", back_populates="documents")


class ProviderSkill(Base):
    __tablename__  = "provider_skills"
    __table_args__ = (UniqueConstraint("provider_id", "category_id"),)
    id          = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    hourly_rate = Column(DECIMAL(10, 2))

    provider    = relationship("Provider", back_populates="skills")
    category    = relationship("Category")


class ProviderAvailability(Base):
    __tablename__ = "provider_availability"
    id          = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    day_of_week = Column(Enum("Mon","Tue","Wed","Thu","Fri","Sat","Sun", name="day_enum"), nullable=False)
    start_time  = Column(Time, nullable=False)
    end_time    = Column(Time, nullable=False)

    provider    = relationship("Provider", back_populates="availability")


class UserLocation(Base):
    __tablename__ = "user_locations"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    label      = Column(String(50))
    address    = Column(Text, nullable=False)
    latitude   = Column(DECIMAL(10, 8))
    longitude  = Column(DECIMAL(11, 8))
    is_default = Column(Boolean, default=False)

    user       = relationship("User", back_populates="locations")


class Coupon(Base):
    __tablename__  = "coupons"
    id             = Column(Integer, primary_key=True, index=True)
    code           = Column(String(30), unique=True, nullable=False)
    discount_type  = Column(Enum("flat", "percent", name="discount_type_enum"), nullable=False)
    discount_value = Column(DECIMAL(10, 2), nullable=False)
    min_order      = Column(DECIMAL(10, 2), default=0)
    max_uses       = Column(Integer, default=100)
    used_count     = Column(Integer, default=0)
    valid_from     = Column(Date)
    valid_until    = Column(Date)
    is_active      = Column(Boolean, default=True)
    created_at     = Column(DateTime, default=func.now())


class Booking(Base):
    __tablename__ = "bookings"
    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider_id         = Column(Integer, ForeignKey("providers.id"), nullable=False)
    service_id          = Column(Integer, ForeignKey("services.id"), nullable=False)
    booking_date        = Column(Date, nullable=False)
    booking_time        = Column(Time, nullable=False)
    address             = Column(Text, nullable=False)
    latitude            = Column(DECIMAL(10, 8))
    longitude           = Column(DECIMAL(11, 8))
    problem_description = Column(Text)
    problem_image       = Column(String(255))
    status              = Column(Enum(BookingStatus), default=BookingStatus.pending)
    is_emergency        = Column(Boolean, default=False)
    coupon_id           = Column(Integer, ForeignKey("coupons.id"), nullable=True)
    base_amount         = Column(DECIMAL(10, 2))
    discount_amount     = Column(DECIMAL(10, 2), default=0)
    final_amount        = Column(DECIMAL(10, 2))
    created_at          = Column(DateTime, default=func.now())
    updated_at          = Column(DateTime, default=func.now(), onupdate=func.now())

    user                = relationship("User", back_populates="bookings")
    provider            = relationship("Provider", back_populates="bookings")
    service             = relationship("Service", back_populates="bookings")
    coupon              = relationship("Coupon")
    status_logs         = relationship("BookingStatusLog", back_populates="booking")
    service_images      = relationship("ServiceImage", back_populates="booking")
    payment             = relationship("Payment", back_populates="booking", uselist=False)
    review              = relationship("Review", back_populates="booking", uselist=False)
    messages            = relationship("ChatMessage", back_populates="booking")
    complaints          = relationship("Complaint", back_populates="booking")


class BookingStatusLog(Base):
    __tablename__ = "booking_status"
    id         = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    status     = Column(String(50), nullable=False)
    changed_at = Column(DateTime, default=func.now())
    note       = Column(Text)

    booking    = relationship("Booking", back_populates="status_logs")


class ServiceImage(Base):
    __tablename__ = "service_images"
    id          = Column(Integer, primary_key=True, index=True)
    booking_id  = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    image_type  = Column(Enum("before", "after", name="image_type_enum"), nullable=False)
    file_path   = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=func.now())

    booking     = relationship("Booking", back_populates="service_images")


class Payment(Base):
    __tablename__       = "payments"
    id                  = Column(Integer, primary_key=True, index=True)
    booking_id          = Column(Integer, ForeignKey("bookings.id"), nullable=False, unique=True)
    amount              = Column(DECIMAL(10, 2), nullable=False)
    payment_method      = Column(Enum(PaymentMethod), nullable=False)
    payment_status      = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    transaction_id      = Column(String(100))
    razorpay_order_id   = Column(String(100))
    paid_at             = Column(DateTime)
    created_at          = Column(DateTime, default=func.now())

    booking             = relationship("Booking", back_populates="payment")


class Transaction(Base):
    __tablename__ = "transactions"
    id          = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    booking_id  = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    amount      = Column(DECIMAL(10, 2), nullable=False)
    type        = Column(Enum("credit", "debit", name="txn_type_enum"), nullable=False)
    description = Column(String(255))
    created_at  = Column(DateTime, default=func.now())

    provider    = relationship("Provider", back_populates="transactions")


class Review(Base):
    __tablename__ = "reviews"
    id          = Column(Integer, primary_key=True, index=True)
    booking_id  = Column(Integer, ForeignKey("bookings.id"), nullable=False, unique=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    rating      = Column(Integer, nullable=False)
    comment     = Column(Text)
    is_flagged  = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=func.now())

    booking     = relationship("Booking", back_populates="review")
    user        = relationship("User", back_populates="reviews")
    provider    = relationship("Provider", back_populates="reviews")


class Favorite(Base):
    __tablename__  = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "provider_id"),)
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    created_at  = Column(DateTime, default=func.now())

    user        = relationship("User", back_populates="favorites")
    provider    = relationship("Provider")


class Notification(Base):
    __tablename__ = "notifications"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    title       = Column(String(150), nullable=False)
    body        = Column(Text)
    is_read     = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=func.now())

    user        = relationship("User", back_populates="notifications")
    provider    = relationship("Provider", back_populates="notifications")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id           = Column(Integer, primary_key=True, index=True)
    booking_id   = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    sender_type  = Column(Enum("user", "provider", name="sender_type_enum"), nullable=False)
    sender_id    = Column(Integer, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.text)
    content      = Column(Text, nullable=False)
    is_read      = Column(Boolean, default=False)
    sent_at      = Column(DateTime, default=func.now())

    booking      = relationship("Booking", back_populates="messages")


class Complaint(Base):
    __tablename__ = "complaints"
    id           = Column(Integer, primary_key=True, index=True)
    booking_id   = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    raised_by    = Column(Enum("user", "provider", name="raised_by_enum"), nullable=False)
    raised_by_id = Column(Integer, nullable=False)
    type         = Column(Enum(ComplaintType), nullable=False)
    description  = Column(Text)
    status       = Column(Enum(ComplaintStatus), default=ComplaintStatus.open)
    created_at   = Column(DateTime, default=func.now())

    booking      = relationship("Booking", back_populates="complaints")
