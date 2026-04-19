from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

connect_args = {}
if settings.database_url.startswith("mysql"):
    connect_args = {
        "charset": "utf8mb4",
        "use_unicode": True,
        "init_command": "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci",
    }

engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# 修复：Python 3.8 不支持泛型注解，直接去掉返回值类型
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()