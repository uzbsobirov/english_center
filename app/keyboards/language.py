from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Tugma matni orqali tilni aniqlaymiz (til tanlashdan oldin bo'lgani uchun
# bu yerda i18n ishlatmaymiz - foydalanuvchi hali birorta tilni tanlamagan)
LANGUAGE_BUTTONS = {
    "🇺🇿 O'zbekcha": "uz",
    "🇷🇺 Русский": "ru",
    "🇬🇧 English": "en",
}


def language_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for text in LANGUAGE_BUTTONS:
        builder.button(text=text)
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)