from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram_i18n import I18nContext
from data.config import WEBAPP_URL

MAIN_MENU_FLUENT_KEYS = [
    "menu-courses",
    "menu-tests",
    "menu-homework",
    "menu-schedule",
    "menu-profile",
    "menu-progress",
    "menu-ranking",
    "menu-referral",
    "menu-language",
    "menu-contact",
    "menu-free-lesson",
]

MAIN_MENU_TEXTS_UZ = [
    "📚 Kurslar", "🎯 Testlar", "📋 Uy Vazifam", "📅 Jadvalim", "👤 Profilim",
    "📊 Progress", "🏆 Reyting", "👥 Referal", "🌐 Til", "📞 Bog'lanish",
    "📝 Free darsga yozilish",
]
MAIN_MENU_TEXTS_RU = [
    "📚 Курсы", "🎯 Тесты", "📋 Домашнее задание", "📅 Расписание", "👤 Мой профиль",
    "📊 Прогресс", "🏆 Рейтинг", "👥 Реферал", "🌐 Язык", "📞 Контакты",
    "📝 Запись на бесплатный урок",
]
MAIN_MENU_TEXTS_EN = [
    "📚 Courses", "🎯 Tests", "📋 Homework", "📅 My Schedule", "👤 My Profile",
    "📊 Progress", "🏆 Ranking", "👥 Referral", "🌐 Language", "📞 Contact",
    "📝 Book free lesson",
]

ALL_MAIN_MENU_TEXTS = set(MAIN_MENU_TEXTS_UZ + MAIN_MENU_TEXTS_RU + MAIN_MENU_TEXTS_EN)


def main_menu_keyboard(i18n: I18nContext) -> ReplyKeyboardMarkup:
    """
    i18n context orqali joriy foydalanuvchi tilida menyu quriladi.
    'Testlar' tugmasi web_app bilan - bosilganda Web App DARHOL ochiladi,
    oraliq xabar yoki qo'shimcha bosish shart emas.
    """
    builder = ReplyKeyboardBuilder()
    for fluent_key in MAIN_MENU_FLUENT_KEYS:
        text = i18n.get(fluent_key)
        if fluent_key == "menu-tests":
            builder.button(text=text, web_app=WebAppInfo(url=WEBAPP_URL))
        else:
            builder.button(text=text)
    builder.adjust(2, 2, 2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)