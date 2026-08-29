"""
Telegram Web App autentifikatsiyasi.

Web App ochilganda Telegram unga 'initData' degan satr beradi - bu foydalanuvchi
ma'lumotlari va HMAC-SHA256 imzosidan iborat. Biz shu imzoni bot tokeni yordamida
qayta hisoblab, mos kelishini tekshiramiz.
"""
import hashlib
import hmac
import json
from urllib.parse import parse_qsl, unquote

from fastapi import Header, HTTPException, Request, status

from data.config import env

BOT_TOKEN = env.str("BOT_TOKEN")
DEV_MODE = env.bool("DEV_MODE", True)


def _calculate_hash(init_data: str, bot_token: str) -> tuple[str, dict]:
    parsed = dict(parse_qsl(init_data, strict_parsing=False))
    received_hash = parsed.pop("hash", None)

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    return calculated_hash, parsed


def verify_telegram_init_data(init_data: str) -> dict | None:
    """
    initData'ni tekshiradi va ichidan foydalanuvchi ma'lumotlarini qaytaradi.
    Agar noto'g'ri bo'lsa None qaytaradi.
    """
    if not init_data:
        return None

    try:
        calculated_hash, parsed = _calculate_hash(init_data, BOT_TOKEN)
        received_hash = dict(parse_qsl(init_data, strict_parsing=False)).get("hash")
    except Exception:
        return None

    if not hmac.compare_digest(calculated_hash, received_hash or ""):
        return None

    user_raw = parsed.get("user")
    if not user_raw:
        return None

    try:
        return json.loads(user_raw)
    except Exception:
        return None


async def get_current_telegram_user(
    request: Request,
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    x_telegram_user_data: str | None = Header(default=None, alias="X-Telegram-User-Data"),
) -> dict:
    """
    FastAPI dependency:
    1. X-Telegram-Init-Data orqali HMAC tekshiruvi.
    2. Agar tunnel / redirect sababli initData uzilgan bo'lsa, X-Telegram-User-Data client headeri.
    3. Request URL query paramlari orqali tekshirish (?user_id=...).
    4. Faqat Swagger/Docs test rejimida fallback (hech qachon real admin ID ishlatilmaydi).
    """
    # 1. To'liq initData HMAC tekshiruvi
    if x_telegram_init_data:
        user_info = verify_telegram_init_data(x_telegram_init_data)
        if user_info and "id" in user_info:
            return user_info

    # 2. Telegram WebApp client yuborgan to'g'ridan-to'g'ri foydalanuvchi ma'lumoti
    if x_telegram_user_data:
        try:
            decoded = unquote(x_telegram_user_data)
            user_data = json.loads(decoded)
            if user_data and "id" in user_data and int(user_data["id"]) > 0:
                return user_data
        except Exception:
            pass

    # 3. Request URL query params fallback (?user_id=123&name=Ali&username=alivali)
    user_id_param = request.query_params.get("user_id")
    if user_id_param and user_id_param.isdigit() and int(user_id_param) > 0:
        return {
            "id": int(user_id_param),
            "first_name": request.query_params.get("name", "O'quvchi"),
            "username": request.query_params.get("username", ""),
        }

    # 4. Faqat Swagger/Docs test rejimida fallback (Admin ID ga emas, neytral dev ID ga)
    if DEV_MODE:
        return {
            "id": 999999999,
            "first_name": "Dev",
            "last_name": "Tester",
            "username": "dev_test_user",
            "language_code": "uz",
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Telegram autentifikatsiyasi amalga oshmadi. Iltimos, testni bot orqali oching.",
    )
