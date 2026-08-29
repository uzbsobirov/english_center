"""
Admin va O'qituvchilar Boshqaruv Paneli (TZ v2.6, 8-bo'lim).
- '👑 Admin Panel' tugmasi yoki /admin komandasi orqali to'liq Admin Reply Menu ochiladi.
- Asosiy o'quvchi menyusi yo'qolib, o'rniga faqat admin/o'qituvchi boshqaruv menyusi chiqadi.
"""
import urllib.parse
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_i18n import I18nContext

from backend.services.user_service import is_admin_or_manager, is_teacher
from app.keyboards.admin_menu import (
    admin_menu_keyboard,
    ADMIN_PANEL_BUTTON_TEXTS,
    ADMIN_MENU_TEXTS,
)
from app.keyboards.main_menu import main_menu_keyboard

router = Router()


@router.message(Command("admin", "dashboard", "panel"))
@router.message(F.text.in_(ADMIN_PANEL_BUTTON_TEXTS))
async def open_admin_panel(message: Message, i18n: I18nContext):
    user_id = message.from_user.id
    is_admin = await is_admin_or_manager(user_id) or await is_teacher(user_id)

    if not is_admin:
        await message.answer("⚠️ Bu bo'lim faqat o'quv markazi ma'muriyati va o'qituvchilari uchun.")
        return

    lang = getattr(i18n, "locale", "uz") or "uz"
    user_name = message.from_user.full_name or "Admin"
    username = message.from_user.username or ""

    reply_kb = admin_menu_keyboard(
        user_id=user_id,
        user_name=user_name,
        username=username,
        lang=lang,
    )

    text = (
        f"👑 <b>Alpha English Center — Boshqaruv Paneli</b>\n\n"
        f"Xush kelibsiz, <b>{user_name}</b>!\n\n"
        f"Quyidagi boshqaruv menyusi faollashtirildi:\n\n"
        f"▫️ <b>📊 Admin Dashboard:</b> Statistika, Guruhlar, O'quvchilar, To'lovlarni tasdiqlash.\n"
        f"▫️ <b>🛠 Test Builder:</b> Yangi CEFR / IELTS savollarini qo'shish va tahrirlash.\n"
        f"▫️ <b>👥 Davomat:</b> Guruhlar bo'yicha davomat olish.\n"
        f"▫️ <b>📋 Uy vazifasi:</b> Dars materiallari va fayllar yuklash.\n"
        f"▫️ <b>💵 Naqd to'lov:</b> O'quvchilardan naqd pul qabul qilish.\n"
        f"▫️ <b>💰 Refund:</b> Pulni qaytarish hisob-kitobi.\n"
        f"▫️ <b>🎓 Sertifikat:</b> Rasmiy PDF sertifikat berish.\n\n"
        f"<i>Ortga qaytish uchun: «◀️ Asosiy menyu» tugmasini bosing.</i>"
    )

    await message.answer(text, reply_markup=reply_kb)


@router.message(F.text == ADMIN_MENU_TEXTS["BACK_TO_MAIN"])
async def back_to_student_menu(message: Message, i18n: I18nContext):
    user_id = message.from_user.id
    is_admin = await is_admin_or_manager(user_id) or await is_teacher(user_id)
    lang = getattr(i18n, "locale", "uz") or "uz"

    kb = main_menu_keyboard(
        i18n=i18n,
        user_id=user_id,
        user_name=message.from_user.full_name,
        username=message.from_user.username,
        lang=lang,
        is_admin=is_admin,
    )

    await message.answer("🏠 <b>Asosiy o'quvchi menyusiga qaytdingiz.</b>", reply_markup=kb)
