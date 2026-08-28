"""
Telegram Web App autentifikatsiyasi.

Web App ochilganda Telegram unga 'initData' degan satr beradi - bu foydalanuvchi
ma'lumotlari va HMAC-SHA256 imzosidan iborat. Biz shu imzoni bot tokeni yordamida
qayta hisoblab, mos kelishini tekshiramiz - shunday qilib so'rov haqiqatan
Telegram orqali kelganini va soxta emasligini bilamiz.

Batafsil: https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
"""
import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, status

from data.config import env

BOT_TOKEN = env.str("BOT_TOKEN")
DEV_MODE = env.bool("DEV_MODE", True)


def _calculate_hash(init_data: str, bot_token: str) -> tuple[str, dict]:
    parsed = dict(parse_qsl(init_data, strict_parsing=True))
    received_hash = parsed.pop("hash", None)

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    return calculated_hash, parsed


def verify_telegram_init_data(init_data: str) -> dict:
    """
    initData'ni tekshiradi va ichidan foydalanuvchi ma'lumotlarini qaytaradi.
    Noto'g'ri bo'lsa xato ko'taradi.
    DEV_MODE bo'lsa va initData bo'lmasa, test foydalanuvchisini qaytaradi.
    """
    if not init_data:
        if DEV_MODE:
            return {
                "id": 1435473812,
                "first_name": "Developer",
                "last_name": "User",
                "username": "developer",
                "language_code": "uz",
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="initData yo'q",
        )

    try:
        calculated_hash, parsed = _calculate_hash(init_data, BOT_TOKEN)
        received_hash = dict(parse_qsl(init_data, strict_parsing=True)).get("hash")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="initData formati noto'g'ri",
        )


    if not hmac.compare_digest(calculated_hash, received_hash or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="initData imzosi noto'g'ri",
        )

    user_raw = parsed.get("user")
    if not user_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Foydalanuvchi ma'lumoti topilmadi",
        )

    return json.loads(user_raw)


async def get_current_telegram_user(
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
) -> dict:
    """
    FastAPI dependency: har bir himoyalangan endpoint shu funksiyani
    parametr sifatida so'rasa, avtomatik autentifikatsiya qilinadi.

    Misol:
        @router.get("/me")
        async def me(user: dict = Depends(get_current_telegram_user)):
            return user
    """
    return verify_telegram_init_data(x_telegram_init_data or "")


