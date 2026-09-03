import urllib.parse
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram_i18n import I18nContext
from data.config import get_webapp_url, ADMINS, DEV_MODE

MAIN_MENU_FLUENT_KEYS = [
    "menu-courses",
    "menu-tests",
    "menu-payments",
    "menu-homework",
    "menu-schedule",
    "menu-profile",
    "menu-progress",
    "menu-ranking",
    "menu-referral",
    "menu-settings",
    "menu-contact",
    "menu-free-lesson",
]

MAIN_MENU_TEXTS_UZ = [
    "📚 Kurslar", "🎯 Testlar", "💳 To'lov", "📋 Uy Vazifam", "📅 Jadvalim", "👤 Profilim",
    "📊 Progress", "🏆 Reyting", "👥 Referal", "⚙️ Sozlamalar", "🌐 Til", "📞 Bog'lanish",
    "📝 Free darsga yozilish",
]
MAIN_MENU_TEXTS_RU = [
    "📚 Курсы", "🎯 Тесты", "💳 Оплата", "📋 Домашнее задание", "📅 Расписание", "👤 Мой профиль",
    "📊 Прогресс", "🏆 Рейтинг", "👥 Реферал", "⚙️ Настройки", "🌐 Язык", "📞 Контакты",
    "📝 Запись на бесплатный урок",
]
MAIN_MENU_TEXTS_EN = [
    "📚 Courses", "🎯 Tests", "💳 Payment", "📋 Homework", "📅 My Schedule", "👤 My Profile",
    "📊 Progress", "🏆 Ranking", "👥 Referral", "⚙️ Settings", "🌐 Language", "📞 Contact",
    "📝 Book free lesson",
]

ALL_MAIN_MENU_TEXTS = set(MAIN_MENU_TEXTS_UZ + MAIN_MENU_TEXTS_RU + MAIN_MENU_TEXTS_EN)


def main_menu_keyboard(
    i18n: I18nContext,
    user_id: int | None = None,
    user_name: str | None = None,
    username: str | None = None,
    lang: str | None = None,
    is_admin: bool = False,
) -> ReplyKeyboardMarkup:
    """
    i18n context orqali joriy foydalanuvchi tilida menyu quriladi.
    'Testlar' tugmasi web_app bilan - bosilganda Web App DARHOL ochiladi.
    Agar foydalanuvchi admin/o'qituvchi bo'lsa, '👑 Admin Panel' tugmasi qo'shiladi.
    """
    builder = ReplyKeyboardBuilder()

    locale_code = lang or getattr(i18n, "locale", "uz") or "uz"
    if not is_admin and user_id:
        env_admin_ids = [int(a) for a in ADMINS if str(a).strip().isdigit()]
        if user_id in env_admin_ids or (DEV_MODE and user_id == 999999999):
            is_admin = True

    app_url = get_webapp_url()
    if app_url and user_id:
        sep = "&" if "?" in app_url else "?"
        params = f"user_id={user_id}&lang={locale_code}"
        if user_name:
            params += f"&name={urllib.parse.quote(str(user_name))}"
        if username:
            params += f"&username={urllib.parse.quote(str(username))}"
        app_url = f"{app_url}{sep}{params}"

    for fluent_key in MAIN_MENU_FLUENT_KEYS:
        text = i18n.get(fluent_key)
        if fluent_key == "menu-tests" and app_url and app_url.startswith("https://"):
            builder.button(text=text, web_app=WebAppInfo(url=app_url))
        else:
            builder.button(text=text)

    if is_admin:
        builder.button(text="👑 Admin Panel")
        builder.adjust(2, 2, 2, 2, 2, 2, 1)
    else:
        builder.adjust(2, 2, 2, 2, 2, 2)

    return builder.as_markup(resize_keyboard=True)