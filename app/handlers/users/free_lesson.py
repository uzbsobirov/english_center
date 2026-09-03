"""
📝 Free darsga yozilish (TZ v2.6, 6.1.1-bo'lim).
- Darajani tanlab mos test orqali free darsga yozilish
"""
import urllib.parse
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram_i18n import I18nContext

from data.config import get_webapp_url

router = Router()

FREE_LESSON_BUTTON_TEXTS = {"📝 Free darsga yozilish", "📝 Запись на бесплатный урок", "📝 Book free lesson"}


@router.message(F.text.in_(FREE_LESSON_BUTTON_TEXTS))
@router.callback_query(F.data == "start_free_trial_flow")
async def start_free_lesson(event: Message | CallbackQuery, i18n: I18nContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 IELTS", callback_data="free_trial_type:IELTS"),
            InlineKeyboardButton(text="🎯 CEFR", callback_data="free_trial_type:CEFR"),
        ],
        [
            InlineKeyboardButton(text="🎯 General English", callback_data="free_trial_type:General"),
        ]
    ])
    text = (
        "📝 <b>Free Darsga Yozilish</b>\n\n"
        "Qaysi yo'nalish bo'yicha tahsil olmoqchisiz?"
    )
    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=keyboard)
        except Exception:
            await event.message.answer(text, reply_markup=keyboard)
        await event.answer()
    else:
        await event.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("free_trial_type:"))
async def free_trial_type_selected(callback: CallbackQuery):
    cert_type = callback.data.split(":")[1]
    levels = ["A1", "A2", "B1", "B2", "C1", "C2"]

    buttons = []
    row = []
    for lvl in levels:
        row.append(InlineKeyboardButton(text=lvl, callback_data=f"free_trial_lvl:{cert_type}:{lvl}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    await callback.message.edit_text(
        f"🎯 Yo'nalish: <b>{cert_type}</b>\n\n"
        f"O'z darajangizni tanlang (shu darajaga mos qisqa test beriladi):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("free_trial_lvl:"))
async def free_trial_level_selected(callback: CallbackQuery, i18n: I18nContext):
    parts = callback.data.split(":")
    cert_type = parts[1]
    level = parts[2]

    # Web App orqali test ochish havolasi (foydalanuvchi ma'lumotlari va joriy til bilan)
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name or ""
    username = callback.from_user.username or ""
    locale_code = getattr(i18n, "locale", "uz") or "uz"

    base_url = get_webapp_url()
    sep = "&" if "?" in base_url else "?"
    test_url = (
        f"{base_url}{sep}level={level}&type={cert_type}&lang={locale_code}"
        f"&user_id={user_id}&name={urllib.parse.quote(user_name)}&username={urllib.parse.quote(username)}"
        f"&is_trial=true"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎯 {level} Testini Boshlash", web_app=WebAppInfo(url=test_url))]
    ])

    await callback.message.edit_text(
        f"🎯 <b>{cert_type} — {level} Daraja Testi</b>\n\n"
        f"Free darsga yozilish uchun ushbu testdan o'tishingiz kerak.\n"
        f"O'tish bali: <b>70%</b>\n\n"
        f"<i>Agar o'ta olmasangiz, tizim avtomatik bir daraja pastroq testni taklif qiladi.</i>",
        reply_markup=keyboard
    )
    await callback.answer()

