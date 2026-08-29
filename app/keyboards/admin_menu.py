import urllib.parse
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from data.config import get_webapp_url

ADMIN_PANEL_BUTTON_TEXTS = {
    "👑 Admin Panel", "👨‍🏫 Boshqaruv Paneli", "👑 Панель управления", "👑 Admin Dashboard",
    "Admin Panel", "Boshqaruv Paneli",
}

ADMIN_MENU_TEXTS = {
    "DASHBOARD": "📊 Admin Dashboard",
    "TEST_BUILDER": "🛠 Test Builder",
    "ATTENDANCE": "👥 Davomat olish",
    "HOMEWORK": "📋 Uy vazifasi qo'shish",
    "CASH_PAYMENT": "💵 Naqd to'lov qabul qilish",
    "REFUND": "💰 Qaytarish (Refund)",
    "CERTIFICATE": "🎓 Sertifikat berish",
    "BACK_TO_MAIN": "◀️ Asosiy menyu",
}


def admin_menu_keyboard(
    user_id: int | None = None,
    user_name: str | None = None,
    username: str | None = None,
    lang: str = "uz",
) -> ReplyKeyboardMarkup:
    """
    Admin va O'qituvchilar uchun maxsus PRO Reply Keyboard.
    Asosiy menyu tugmalarini butunlay almashtiradi va barcha boshqaruv funksiyalarini taqdim etadi.
    """
    builder = ReplyKeyboardBuilder()

    base_url = get_webapp_url()
    sep = "&" if "?" in base_url else "?"
    name_param = urllib.parse.quote(str(user_name or "Admin"))
    user_param = urllib.parse.quote(str(username or ""))

    admin_web_url = (
        f"{base_url}{sep}mode=admin&user_id={user_id}&lang={lang}"
        f"&name={name_param}&username={user_param}"
    )

    teacher_web_url = (
        f"{base_url}{sep}mode=teacher&user_id={user_id}&lang={lang}"
        f"&name={name_param}&username={user_param}"
    )

    # 1-Qator: 2 ta to'g'ridan-to'g'ri Web App
    if admin_web_url.startswith("https://"):
        builder.button(text=ADMIN_MENU_TEXTS["DASHBOARD"], web_app=WebAppInfo(url=admin_web_url))
    else:
        builder.button(text=ADMIN_MENU_TEXTS["DASHBOARD"])

    if teacher_web_url.startswith("https://"):
        builder.button(text=ADMIN_MENU_TEXTS["TEST_BUILDER"], web_app=WebAppInfo(url=teacher_web_url))
    else:
        builder.button(text=ADMIN_MENU_TEXTS["TEST_BUILDER"])

    # 2-Qator: Davomat va Uy vazifasi
    builder.button(text=ADMIN_MENU_TEXTS["ATTENDANCE"])
    builder.button(text=ADMIN_MENU_TEXTS["HOMEWORK"])

    # 3-Qator: Moliya (To'lov va Refund)
    builder.button(text=ADMIN_MENU_TEXTS["CASH_PAYMENT"])
    builder.button(text=ADMIN_MENU_TEXTS["REFUND"])

    # 4-Qator: Sertifikat
    builder.button(text=ADMIN_MENU_TEXTS["CERTIFICATE"])

    # 5-Qator: Chiqish / Asosiy menyu
    builder.button(text=ADMIN_MENU_TEXTS["BACK_TO_MAIN"])

    builder.adjust(2, 2, 2, 1, 1)
    return builder.as_markup(resize_keyboard=True)
