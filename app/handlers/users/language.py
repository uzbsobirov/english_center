"""
🌐 Tilni o'zgartirish (TZ v2.6, 3-bo'lim).
- Istalgan vaqtda 🇺🇿 O'zbek / 🇷🇺 Rus / 🇬🇧 Ingliz tiliga o'tkazish
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_i18n import I18nContext
from sqlalchemy import update

from backend.database import async_session
from backend.models import User, LanguageEnum
from app.keyboards.main_menu import main_menu_keyboard

router = Router()

LANGUAGE_BUTTON_TEXTS = {"🌐 Til", "🌐 Язык", "🌐 Language"}


@router.message(F.text.in_(LANGUAGE_BUTTON_TEXTS))
async def language_menu(message: Message, i18n: I18nContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbek tili", callback_data="switch_lang:uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский язык", callback_data="switch_lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="switch_lang:en")],
    ])
    await message.answer("🌐 Qaysi tilga o'zgartirmoqchisiz? / Выберите язык / Select language:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("switch_lang:"))
async def switch_language(callback: CallbackQuery, i18n: I18nContext):
    lang = callback.data.split(":")[1]
    user_id = callback.from_user.id

    async with async_session() as session:
        await session.execute(
            update(User).where(User.id == user_id).values(language=LanguageEnum(lang))
        )
        await session.commit()

    await i18n.set_locale(lang, event_from_user=callback.from_user)

    msg_map = {
        "uz": "Til muvaffaqiyatli o'zgartirildi! 🇺🇿",
        "ru": "Язык успешно изменен! 🇷🇺",
        "en": "Language successfully changed! 🇬🇧",
    }
    await callback.message.delete()
    await callback.message.answer(
        msg_map.get(lang, "OK"),
        reply_markup=main_menu_keyboard(
            i18n,
            user_id=callback.from_user.id,
            user_name=callback.from_user.full_name,
            username=callback.from_user.username,
        ),
    )
    await callback.answer()
