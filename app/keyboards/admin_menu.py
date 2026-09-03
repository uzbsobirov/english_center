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
    "TEACHER_DASHBOARD": "👨‍🏫 O'qituvchi Kabineti",
    "TEST_BUILDER": "🛠 Test Builder",
    "ATTENDANCE": "👥 Davomat olish",
    "HOMEWORK": "📋 Uy vazifasi qo'shish",
    "CASH_PAYMENT": "💵 Naqd to'lov qabul qilish",
    "REFUND": "💰 Qaytarish (Refund)",
    "CERTIFICATE": "🎓 Sertifikat berish",
    "BROADCAST": "📢 Xabar yuborish (Broadcast)",
    "TEACHERS": "👨‍🏫 O'qituvchilar",
    "ADMINS": "👑 Adminlar",
    "BACK_TO_MAIN": "◀️ Asosiy menyu",
}


def admin_menu_keyboard(
    user_id: int | None = None,
    user_name: str | None = None,
    username: str | None = None,
    lang: str = "uz",
    is_admin: bool = True,
    is_teacher: bool = False,
) -> ReplyKeyboardMarkup:
    """
    Admin va O'qituvchilar uchun maxsus PRO Reply Keyboard.
    - Faqat O'qituvchi: faqat O'qituvchi Kabineti va sinf vositalari.
    - Faqat Admin: faqat Admin Dashboard va boshqaruv vositalari.
    - Ikkalasi ham bo'lsa (Dual-role): ikkalasiga ham to'liq kirish.
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

    builder_web_url = (
        f"{base_url}{sep}mode=builder&user_id={user_id}&lang={lang}"
        f"&name={name_param}&username={user_param}"
    )

    # 1. FAQAT O'QITUVCHI BO'LSA
    if not is_admin and is_teacher:
        if teacher_web_url.startswith("https://"):
            builder.button(text=ADMIN_MENU_TEXTS["TEACHER_DASHBOARD"], web_app=WebAppInfo(url=teacher_web_url))
        else:
            builder.button(text=ADMIN_MENU_TEXTS["TEACHER_DASHBOARD"])

        if builder_web_url.startswith("https://"):
            builder.button(text=ADMIN_MENU_TEXTS["TEST_BUILDER"], web_app=WebAppInfo(url=builder_web_url))
        else:
            builder.button(text=ADMIN_MENU_TEXTS["TEST_BUILDER"])

        builder.button(text=ADMIN_MENU_TEXTS["ATTENDANCE"])
        builder.button(text=ADMIN_MENU_TEXTS["HOMEWORK"])
        builder.button(text=ADMIN_MENU_TEXTS["CERTIFICATE"])
        builder.button(text=ADMIN_MENU_TEXTS["BACK_TO_MAIN"])

        builder.adjust(2, 2, 1, 1)
        return builder.as_markup(resize_keyboard=True)

    # 2. FAQAT ADMIN BO'LSA (O'QITUVCHI EMAS)
    if is_admin and not is_teacher:
        if admin_web_url.startswith("https://"):
            builder.button(text=ADMIN_MENU_TEXTS["DASHBOARD"], web_app=WebAppInfo(url=admin_web_url))
        else:
            builder.button(text=ADMIN_MENU_TEXTS["DASHBOARD"])

        builder.button(text=ADMIN_MENU_TEXTS["CASH_PAYMENT"])
        builder.button(text=ADMIN_MENU_TEXTS["REFUND"])
        builder.button(text=ADMIN_MENU_TEXTS["TEACHERS"])
        builder.button(text=ADMIN_MENU_TEXTS["ADMINS"])
        builder.button(text=ADMIN_MENU_TEXTS["BROADCAST"])
        builder.button(text=ADMIN_MENU_TEXTS["BACK_TO_MAIN"])

        builder.adjust(1, 2, 2, 1, 1)
        return builder.as_markup(resize_keyboard=True)

    # 3. HAM ADMIN, HAM O'QITUVCHI BO'LSA (IKKALASIGA HAM TO'LIQ KIRISH)
    if admin_web_url.startswith("https://"):
        builder.button(text=ADMIN_MENU_TEXTS["DASHBOARD"], web_app=WebAppInfo(url=admin_web_url))
    else:
        builder.button(text=ADMIN_MENU_TEXTS["DASHBOARD"])

    if teacher_web_url.startswith("https://"):
        builder.button(text=ADMIN_MENU_TEXTS["TEACHER_DASHBOARD"], web_app=WebAppInfo(url=teacher_web_url))
    else:
        builder.button(text=ADMIN_MENU_TEXTS["TEACHER_DASHBOARD"])

    builder.button(text=ADMIN_MENU_TEXTS["ATTENDANCE"])
    builder.button(text=ADMIN_MENU_TEXTS["HOMEWORK"])
    builder.button(text=ADMIN_MENU_TEXTS["CASH_PAYMENT"])
    builder.button(text=ADMIN_MENU_TEXTS["REFUND"])
    builder.button(text=ADMIN_MENU_TEXTS["TEACHERS"])
    builder.button(text=ADMIN_MENU_TEXTS["ADMINS"])
    builder.button(text=ADMIN_MENU_TEXTS["CERTIFICATE"])
    builder.button(text=ADMIN_MENU_TEXTS["BROADCAST"])
    builder.button(text=ADMIN_MENU_TEXTS["BACK_TO_MAIN"])

    builder.adjust(2, 2, 2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)
