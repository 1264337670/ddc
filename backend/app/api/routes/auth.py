from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional
import re

from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.db.models import User
from app.db.schemas import LoginRequest, RegisterRequest, TokenResponse, UserPublic

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = value.strip()
    return text or None


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    account = payload.account.strip()
    nickname = payload.nickname.strip()
    password = payload.password.strip()

    if len(password) < 6 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="密码需至少6位，且必须包含字母和数字")

    existing_account = db.execute(select(User).where(User.account == account)).scalar_one_or_none()
    if existing_account:
        raise HTTPException(status_code=400, detail="Account already exists")

    if payload.email:
        existing_email = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")

    phone = _normalize_text(payload.phone)
    if phone:
        existing_phone = db.execute(select(User).where(User.phone == phone)).scalar_one_or_none()
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone already exists")

    user = User(
        account=account,
        password_hash=hash_password(password),
        nickname=nickname,
        avatar=_normalize_text(payload.avatar),
        xhs_url=_normalize_text(payload.xhs_url),
        email=payload.email,
        gender=_normalize_text(payload.gender),
        phone=phone,
        signature=_normalize_text(payload.signature),
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.account)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    account = payload.account.strip()
    user = db.execute(select(User).where(User.account == account, User.is_active == True)).scalar_one_or_none()  # noqa: E712
    if not user:
        raise HTTPException(status_code=401, detail="Invalid account or password")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid account or password")

    token = create_access_token(user.account)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))
