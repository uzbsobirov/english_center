from aiogram import Router, F
from aiogram_i18n import I18nContext
from aiogram.types import Message

from app.keyboards.main_menu import ALL_MAIN_MENU_TEXTS

router = Router()


@router.message(F.text.in_(ALL_MAIN_MENU_TEXTS))
async def main_menu_placeholder(message: Message, i18n: I18nContext):
    """
    Asosiy menyu tugmalari uchun vaqtinchalik javob.
    ('Testlar' tugmasi endi web_app orqali to'g'ridan-to'g'ri ochiladi,
    shuning uchun bu handler'ga umuman kelmaydi.)
    Har bir tugma TZ'dagi tegishli bosqichga yetganda
    shu handler o'rniga haqiqiy funksiyaga almashtiriladi.
    """
    await message.answer(i18n.get("coming-soon"))