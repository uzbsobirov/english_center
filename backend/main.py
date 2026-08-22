"""
FastAPI backend - Web App uchun API.
Bot (aiogram) va bu backend bir xil PostgreSQL bazaga ulanadi,
lekin ikkalasi alohida process sifatida ishga tushiriladi.

Ishga tushirish:
    uvicorn backend.main:app --reload --port 8000
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from backend.deps import get_current_telegram_user

app = FastAPI(title="English Center API")

# Web App boshqa domendan (Telegram ichida) so'rov yuboradi,
# shuning uchun CORS ruxsat berilishi kerak.
# Productionda allow_origins ni aniq domen bilan cheklash tavsiya etiladi.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Server ishlab turganini tekshirish uchun oddiy endpoint."""
    return {"status": "ok"}


@app.get("/api/me")
async def me(user: dict = Depends(get_current_telegram_user)):
    """
    Test endpoint: Web App'dan initData bilan so'rov kelsa,
    Telegram foydalanuvchi ma'lumotini qaytaradi.
    Bu orqali autentifikatsiya ishlayotganini tekshiramiz.
    """
    return {"telegram_user": user}