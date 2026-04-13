from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# 修复：Python 3.8 不支持泛型注解，直接去掉返回值类型
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()