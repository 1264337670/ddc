from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        account = payload.get("sub")
        if not isinstance(account, str) or not account:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    stmt = select(User).where(User.account == account, User.is_active == True)  # noqa: E712
    user = db.execute(stmt).scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user
