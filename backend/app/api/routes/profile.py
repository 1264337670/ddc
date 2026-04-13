from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.db.schemas import ProfileUpdateRequest, UserPublic

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = value.strip()
    return text or None


@router.get("/me", response_model=UserPublic)
def get_my_profile(current_user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(current_user)


@router.put("/me", response_model=UserPublic)
def update_my_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPublic:
    if payload.email and payload.email != current_user.email:
        existing_email = db.execute(select(User).where(User.email == payload.email, User.id != current_user.id)).scalar_one_or_none()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")

    phone = _normalize_text(payload.phone)
    if phone and phone != current_user.phone:
        existing_phone = db.execute(select(User).where(User.phone == phone, User.id != current_user.id)).scalar_one_or_none()
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone already exists")

    if payload.nickname is not None:
        current_user.nickname = payload.nickname.strip()
    if payload.avatar is not None:
        current_user.avatar = _normalize_text(payload.avatar)
    if payload.xhs_url is not None:
        current_user.xhs_url = _normalize_text(payload.xhs_url)
    if payload.email is not None:
        current_user.email = payload.email
    if payload.gender is not None:
        current_user.gender = _normalize_text(payload.gender)
    if payload.phone is not None:
        current_user.phone = phone
    if payload.signature is not None:
        current_user.signature = _normalize_text(payload.signature)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return UserPublic.model_validate(current_user)
