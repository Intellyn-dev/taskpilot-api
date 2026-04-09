from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserProfile

router = APIRouter()


@router.get("/")
def list_users(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return [{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in users]


@router.post("/")
def create_user(name: str, email: str, role: str = "member", db: Session = Depends(get_db)):
    user = User(name=name, email=email, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email}


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "avatar_url": user.profile.avatar_url if user.profile else None,
        "bio": user.profile.bio if user.profile else None,
        "company": user.company.name if user.company else None,
    }


@router.put("/{user_id}/profile")
def update_profile(user_id: int, bio: str = "", avatar_url: str = "", db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.profile:
        user.profile.bio = bio
        user.profile.avatar_url = avatar_url
    else:
        profile = UserProfile(user_id=user_id, bio=bio, avatar_url=avatar_url)
        db.add(profile)
    db.commit()
    return {"user_id": user_id, "bio": bio, "avatar_url": avatar_url}
