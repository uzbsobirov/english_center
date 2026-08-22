from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# TZ v2.4, 16-bo'lim: Asosiy menyu tugmalari (UZ/RU/EN)
MAIN_MENU_BUTTONS = {
    "courses": {"uz": "📚 Kurslar", "ru": "📚 Курсы", "en": "📚 Courses"},
    "tests": {"uz": "🎯 Testlar", "ru": "🎯 Тесты", "en": "🎯 Tests"},
    "homework": {"uz": "📋 Uy Vazifam", "ru": "📋 Домашнее задание", "en": "📋 Homework"},
    "schedule": {"uz": "📅 Jadvalim", "ru": "📅 Расписание", "en": "📅 My Schedule"},
    "profile": {"uz": "👤 Profilim", "ru": "👤 Мой профиль", "en": "👤 My Profile"},
    "progress": {"uz": "📊 Progress", "ru": "📊 Прогресс", "en": "📊 Progress"},
    "ranking": {"uz": "🏆 Reyting", "ru": "🏆 Рейтинг", "en": "🏆 Ranking"},
    "referral": {"uz": "👥 Referal", "ru": "👥 Реферал", "en": "👥 Referral"},
    "language": {"uz": "🌐 Til", "ru": "🌐 Язык", "en": "🌐 Language"},
    "contact": {"uz": "📞 Bog'lanish", "ru": "📞 Контакты", "en": "📞 Contact"},
    "free_lesson": {
        "uz": "📝 Free darsga yozilish",
        "ru": "📝 Запись на бесплатный урок",
        "en": "📝 Book free lesson",
    },
}


def main_menu_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for key, translations in MAIN_MENU_BUTTONS.items():
        builder.button(text=translations.get(lang, translations["uz"]))
    builder.adjust(2, 2, 2, 2, 2, 1)  # 11 ta tugma: 5 qator x2 + oxirgi 1 ta
    return builder.as_markup(resize_keyboard=True)