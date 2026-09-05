"""
FastAPI backend - Web App uchun API.
...
"""
import logging
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from backend.deps import get_current_telegram_user
from backend.database import async_session
from backend.models import User, LanguageEnum, RoleEnum
from backend.api.routes import tests, courses, teacher, admin, student, payments

logger = logging.getLogger(__name__)

app = FastAPI(title="English Center API", version="2.6")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.error(f"Database integrity error on {request.method} {request.url.path}: {exc}")
    orig_msg = str(getattr(exc, "orig", exc)).lower()
    
    if "foreign key" in orig_msg:
        detail = "Bog'langan obyekt (foydalanuvchi, guruh yoki kurs) topilmadi yoki noto'g'ri ko'rsatilgan."
    elif "unique" in orig_msg:
        detail = "Ushbu ma'lumot allaqachon tizimda mavjud (takroriy yozuv)."
    else:
        detail = "Ma'lumotlar bazasida bog'liqlik yoki unikal qiymat cheklovi xatosi yuz berdi."

    return JSONResponse(status_code=400, content={"status": "error", "detail": detail})


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.6"}


@app.get("/api/me")
async def me(user: dict = Depends(get_current_telegram_user)):
    user_lang = "uz"
    user_role = "student"
    async with async_session() as session:
        db_user = await session.get(User, user["id"])
        if db_user:
            user_lang = db_user.language.value if db_user.language else "uz"
            user_role = db_user.role.value if db_user.role else "student"
    return {
        "telegram_user": user,
        "language": user_lang,
        "role": user_role,
    }


class UserLanguagePayload(BaseModel):
    language: str


@app.post("/api/user/language")
@app.put("/api/user/language")
async def update_user_language(
    payload: UserLanguagePayload,
    user: dict = Depends(get_current_telegram_user),
):
    lang = payload.language.lower().strip()
    if lang not in ("uz", "ru", "en"):
        raise HTTPException(status_code=400, detail="Faqat 'uz', 'ru' yoki 'en' tillari qabul qilinadi.")

    async with async_session() as session:
        db_user = await session.get(User, user["id"])
        if db_user:
            db_user.language = LanguageEnum(lang)
            await session.commit()
        else:
            db_user = User(
                id=user["id"],
                full_name=user.get("first_name", "Foydalanuvchi"),
                username=user.get("username"),
                language=LanguageEnum(lang),
                role=RoleEnum.student,
            )
            session.add(db_user)
            await session.commit()

    return {"status": "success", "language": lang, "message": "Til muvaffaqiyatli saqlandi!"}


# Routers
app.include_router(tests.router)
app.include_router(courses.router)
app.include_router(teacher.router)
app.include_router(admin.router)
app.include_router(student.router)
app.include_router(payments.router)


