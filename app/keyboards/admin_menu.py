import urllib.parse
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from data.config import get_webapp_url

ADMIN_PANEL_BUTTON_TEXTS = {
    "👑 Admin Panel", "👨‍🏫 Boshqaruv Paneli", "👑 Панель управления", "👑 Admin Dashboard",
    "Admin Panel", "Boshqaruv Paneli",
}

ADMIN_MENU_TEXTS_BY_LANG = {
    "uz": {
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
    },
    "ru": {
        "DASHBOARD": "📊 Панель админа",
        "TEACHER_DASHBOARD": "👨‍🏫 Кабинет учителя",
        "TEST_BUILDER": "🛠 Конструктор тестов",
        "ATTENDANCE": "👥 Отметить посещаемость",
        "HOMEWORK": "📋 Добавить Д/З",
        "CASH_PAYMENT": "💵 Прием наличных",
        "REFUND": "💰 Возврат (Refund)",
        "CERTIFICATE": "🎓 Выдать сертификат",
        "BROADCAST": "📢 Рассылка (Broadcast)",
        "TEACHERS": "👨‍🏫 Преподаватели",
        "ADMINS": "👑 Администраторы",
        "BACK_TO_MAIN": "◀️ Главное меню",
    },
    "en": {
        "DASHBOARD": "📊 Admin Dashboard",
        "TEACHER_DASHBOARD": "👨‍🏫 Teacher Cabinet",
        "TEST_BUILDER": "🛠 Test Builder",
        "ATTENDANCE": "👥 Take Attendance",
        "HOMEWORK": "📋 Add Homework",
        "CASH_PAYMENT": "💵 Receive Cash Payment",
        "REFUND": "💰 Refund Management",
        "CERTIFICATE": "🎓 Issue Certificate",
        "BROADCAST": "📢 Send Broadcast",
        "TEACHERS": "👨‍🏫 Teachers",
        "ADMINS": "👑 Admins",
        "BACK_TO_MAIN": "◀️ Main Menu",
    },
}

# Standart UZ lug'ati (orqaga moslik uchun)
ADMIN_MENU_TEXTS = ADMIN_MENU_TEXTS_BY_LANG["uz"]

# Barcha tillardagi tugma to'plamlari (Aiogram filtrlarida ushlash uchun)
ALL_BACK_BUTTONS = {
    "◀️ Asosiy menyu", "◀️ Главное меню", "◀️ Main Menu", "◀️ Main menu",
    "Asosiy menyu", "Главное меню", "Main Menu",
}
ALL_ADMINS_BUTTONS = {
    "👑 Adminlar", "👑 Администраторы", "👑 Admins",
    "Adminlar", "Администраторы", "Admins",
}
ALL_TEACHERS_BUTTONS = {
    "👨‍🏫 O'qituvchilar", "👨‍🏫 Преподаватели", "👨‍🏫 Teachers",
    "O'qituvchilar", "Преподаватели", "Teachers",
}
ALL_ATTENDANCE_BUTTONS = {
    "👥 Davomat olish", "👥 Отметить посещаемость", "👥 Take Attendance",
    "👥 Davomat", "Davomat", "Attendance", "Посещаемость",
}
ALL_HOMEWORK_BUTTONS = {
    "📋 Uy vazifasi qo'shish", "📋 Добавить Д/З", "📋 Add Homework",
    "📋 Uy vazifasi yuklash", "Uy vazifasi qo'shish", "Homework", "Домашнее задание",
}
ALL_CASH_BUTTONS = {
    "💵 Naqd to'lov qabul qilish", "💵 Прием наличных", "💵 Receive Cash Payment",
    "💵 Naqd to'lov", "Naqd to'lov", "Cash payment", "Прием наличных",
}
ALL_REFUND_BUTTONS = {
    "💰 Qaytarish (Refund)", "💰 Возврат (Refund)", "💰 Refund Management",
    "💰 Qaytarish", "Refund", "Qaytarish", "Возврат",
}
ALL_CERTIFICATE_BUTTONS = {
    "🎓 Sertifikat berish", "🎓 Выдать сертификат", "🎓 Issue Certificate",
    "🎓 Sertifikat", "Sertifikat berish", "Certificate", "Сертификат",
}
ALL_BROADCAST_BUTTONS = {
    "📢 Xabar yuborish (Broadcast)", "📢 Рассылка (Broadcast)", "📢 Send Broadcast",
    "📢 Xabar yuborish", "Xabar yuborish", "Broadcast", "Рассылка",
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

    texts = ADMIN_MENU_TEXTS_BY_LANG.get(lang, ADMIN_MENU_TEXTS_BY_LANG["uz"])

    # 1. FAQAT O'QITUVCHI BO'LSA
    if not is_admin and is_teacher:
        if teacher_web_url.startswith("https://"):
            builder.button(text=texts["TEACHER_DASHBOARD"], web_app=WebAppInfo(url=teacher_web_url))
        else:
            builder.button(text=texts["TEACHER_DASHBOARD"])

        if builder_web_url.startswith("https://"):
            builder.button(text=texts["TEST_BUILDER"], web_app=WebAppInfo(url=builder_web_url))
        else:
            builder.button(text=texts["TEST_BUILDER"])

        builder.button(text=texts["ATTENDANCE"])
        builder.button(text=texts["HOMEWORK"])
        builder.button(text=texts["CERTIFICATE"])
        builder.button(text=texts["BACK_TO_MAIN"])

        builder.adjust(2, 2, 1, 1)
        return builder.as_markup(resize_keyboard=True)

    # 2. FAQAT ADMIN BO'LSA (O'QITUVCHI EMAS)
    if is_admin and not is_teacher:
        if admin_web_url.startswith("https://"):
            builder.button(text=texts["DASHBOARD"], web_app=WebAppInfo(url=admin_web_url))
        else:
            builder.button(text=texts["DASHBOARD"])

        builder.button(text=texts["CASH_PAYMENT"])
        builder.button(text=texts["REFUND"])
        builder.button(text=texts["TEACHERS"])
        builder.button(text=texts["ADMINS"])
        builder.button(text=texts["BROADCAST"])
        builder.button(text=texts["BACK_TO_MAIN"])

        builder.adjust(1, 2, 2, 1, 1)
        return builder.as_markup(resize_keyboard=True)

    # 3. HAM ADMIN, HAM O'QITUVCHI BO'LSA (IKKALASIGA HAM TO'LIQ KIRISH)
    if admin_web_url.startswith("https://"):
        builder.button(text=texts["DASHBOARD"], web_app=WebAppInfo(url=admin_web_url))
    else:
        builder.button(text=texts["DASHBOARD"])

    if teacher_web_url.startswith("https://"):
        builder.button(text=texts["TEACHER_DASHBOARD"], web_app=WebAppInfo(url=teacher_web_url))
    else:
        builder.button(text=texts["TEACHER_DASHBOARD"])

    builder.button(text=texts["ATTENDANCE"])
    builder.button(text=texts["HOMEWORK"])
    builder.button(text=texts["CASH_PAYMENT"])
    builder.button(text=texts["REFUND"])
    builder.button(text=texts["TEACHERS"])
    builder.button(text=texts["ADMINS"])
    builder.button(text=texts["CERTIFICATE"])
    builder.button(text=texts["BROADCAST"])
    builder.button(text=texts["BACK_TO_MAIN"])

    builder.adjust(2, 2, 2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)
