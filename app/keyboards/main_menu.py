from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram_i18n import I18nContext

# Fluent kalitlar - klaviaturani i18n orqali qurish uchun
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

# 3 tilning aniq matnlari - handler'da F.text.in_() filtri uchun kerak
# (bot.ftl fayllardagi qiymatlar bilan bir xil bo'lishi shart)
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
    Til aniqlash butunlay middleware zimmasida - bu yerda hech narsa
    qo'lda uzatilmaydi.
    """
    builder = ReplyKeyboardBuilder()
    for fluent_key in MAIN_MENU_FLUENT_KEYS:
        builder.button(text=i18n.get(fluent_key))
    builder.adjust(2, 2, 2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)