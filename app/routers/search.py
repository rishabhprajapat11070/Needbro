from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional
from app.database.connection import get_db
from app.models.models import Provider, Category, Service, ProviderSkill
from app.schemas.schemas import CategoryOut, ServiceOut
import math

router = APIRouter(prefix="/api", tags=["Search & Categories"])


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Calculate distance in km between two coordinates."""
    R = 6371
    phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).filter(Category.is_active == True).all()


@router.get("/categories/{category_id}/services", response_model=list[ServiceOut])
def list_services(category_id: int, db: Session = Depends(get_db)):
    return db.query(Service).filter(
        Service.category_id == category_id,
        Service.is_active == True
    ).all()


@router.get("/search")
def search_providers(
    query: Optional[str] = None,
    category_id: Optional[int] = None,
    min_rating: Optional[float] = None,
    max_distance_km: Optional[float] = None,
    user_lat: Optional[float] = None,
    user_lng: Optional[float] = None,
    available_today: Optional[bool] = None,
    verified_only: Optional[bool] = None,
    sort_by: Optional[str] = "rating",  # rating | distance | price
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    q = db.query(Provider).filter(Provider.is_active == True)

    # Filter by category (via skills)
    if category_id:
        q = q.join(ProviderSkill).filter(ProviderSkill.category_id == category_id)

    # Filter by name search
    if query:
        q = q.filter(Provider.name.ilike(f"%{query}%"))

    # Filter verified only
    if verified_only:
        q = q.filter(Provider.is_verified == True)

    # Filter by minimum rating
    if min_rating:
        q = q.filter(Provider.avg_rating >= min_rating)

    # Available now
    if available_today:
        q = q.filter(Provider.availability_status == "online")

    providers = q.all()

    # Distance filtering & sorting (in-memory since MySQL lacks built-in haversine)
    results = []
    for p in providers:
        dist = None
        if user_lat and user_lng and p.latitude and p.longitude:
            dist = haversine_km(user_lat, user_lng, p.latitude, p.longitude)
            if max_distance_km and dist > max_distance_km:
                continue

        results.append({
            "id": p.id,
            "name": p.name,
            "photo": p.photo,
            "experience_years": p.experience_years,
            "avg_rating": float(p.avg_rating),
            "total_jobs": p.total_jobs,
            "availability_status": p.availability_status,
            "is_verified": p.is_verified,
            "distance_km": round(dist, 2) if dist is not None else None,
        })

    # Sort
    if sort_by == "distance" and user_lat:
        results.sort(key=lambda x: x["distance_km"] or 999)
    else:
        results.sort(key=lambda x: x["avg_rating"], reverse=True)

    # Paginate
    start = (page - 1) * limit
    return {
        "total": len(results),
        "page": page,
        "results": results[start: start + limit],
    }


@router.get("/providers/{provider_id}")
def get_provider_detail(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        from fastapi import HTTPException
        raise HTTPException(404, "Provider not found")

    skills = [{"category": s.category.name, "hourly_rate": float(s.hourly_rate or 0)}
              for s in provider.skills]

    recent_reviews = []
    for r in provider.reviews[-5:]:
        recent_reviews.append({
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat(),
        })

    return {
        "id": provider.id,
        "name": provider.name,
        "photo": provider.photo,
        "experience_years": provider.experience_years,
        "bio": provider.bio,
        "shop_address": provider.shop_address,
        "is_verified": provider.is_verified,
        "availability_status": provider.availability_status,
        "avg_rating": float(provider.avg_rating),
        "total_jobs": provider.total_jobs,
        "skills": skills,
        "recent_reviews": recent_reviews,
    }
