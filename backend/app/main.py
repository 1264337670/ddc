from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from typing import Dict
from pathlib import Path

from app.api.routes.auth import router as auth_router
from app.api.routes.admin import router as admin_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.chat import router as chat_router
from app.api.routes.mentor import router as mentor_router
from app.api.routes.profile import router as profile_router
from app.api.routes.tree_hole import router as tree_hole_router
from app.core.config import settings

BACKEND_ROOT = Path(__file__).resolve().parents[1]
AVATAR_DIR = BACKEND_ROOT / "avatar_uploads"
SHOW_DIR = BACKEND_ROOT / "show"
WORD_DIR = BACKEND_ROOT / "word"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
SHOW_DIR.mkdir(parents=True, exist_ok=True)
WORD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=settings.app_name)

origins = [item.strip() for item in settings.cors_origins.split(",") if item.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/avatar-files", StaticFiles(directory=str(AVATAR_DIR)), name="avatar-files")
app.mount("/show", StaticFiles(directory=str(SHOW_DIR)), name="analysis-show")
app.mount("/word", StaticFiles(directory=str(WORD_DIR)), name="analysis-word")


@app.exception_handler(OperationalError)
async def handle_db_operational_error(_, exc: OperationalError):
    return JSONResponse(
        status_code=503,
        content={
            "detail": "数据库连接失败，请检查 DATABASE_URL 中的账号、密码、主机和权限",
            "error": str(exc.orig) if getattr(exc, "orig", None) else str(exc),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def handle_db_error(_, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "数据库请求异常",
            "error": str(exc),
        },
    )


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(tree_hole_router)
app.include_router(mentor_router)
app.include_router(analysis_router)
app.include_router(chat_router)
app.include_router(admin_router)
