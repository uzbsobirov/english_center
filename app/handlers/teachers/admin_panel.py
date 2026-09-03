"""
Admin va O'qituvchilar Boshqaruv Paneli (TZ v2.6, 8-bo'lim).
- '👑 Admin Panel' tugmasi yoki /admin komandasi orqali to'liq Admin Reply Menu ochiladi.
- Asosiy o'quvchi menyusi yo'qolib, o'rniga faqat admin/o'qituvchi boshqaruv menyusi chiqadi.
"""
import urllib.parse
from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram_i18n import I18nContext

from backend.services.user_service import is_admin_or_manager, is_teacher, add_admin, remove_admin
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
    is_real_admin = await is_admin_or_manager(user_id)
    is_teacher_user = await is_teacher(user_id)

    if not is_real_admin and not is_teacher_user:
        await message.answer("⚠️ Bu bo'lim faqat o'quv markazi ma'muriyati va o'qituvchilari uchun.")
        return

    lang = getattr(i18n, "locale", "uz") or "uz"
    user_name = message.from_user.full_name or "Ustoz"
    username = message.from_user.username or ""

    reply_kb = admin_menu_keyboard(
        user_id=user_id,
        user_name=user_name,
        username=username,
        lang=lang,
        is_admin=is_real_admin,
        is_teacher=is_teacher_user,
    )

    if not is_real_admin:
        # FAQAT O'QITUVCHILAR UCHUN XABAR (MOLIYA VA SOZLAMALARSIZ)
        text = (
            f"👨‍🏫 <b>Alpha English Center — O'qituvchi Kabineti</b>\n\n"
            f"Assalomu alaykum, <b>{user_name}</b>!\n"
            f"Sizning o'qituvchilik ishchi kabinetingiz faollashtirildi:\n\n"
            f"▫️ <b>👨‍🏫 O'qituvchi Kabineti (Web):</b> Sizga biriktirilgan dars guruhlari, o'quvchilar ro'yxati va dars jadvali.\n"
            f"▫️ <b>👥 Davomat:</b> Darsga kelgan va kelmagan o'quvchilarni belgilash.\n"
            f"▫️ <b>📋 Uy Vazifasi:</b> Vazifalar yuklash (o'quvchilarga avtomatik xabar boradi).\n"
            f"▫️ <b>🛠 Test Builder & AI:</b> Sun'iy intellekt (Gemini) yordamida testlar yaratish.\n"
            f"▫️ <b>🎓 Sertifikat:</b> Bitiruvchilarga rasmiy PDF sertifikat berish.\n\n"
            f"<i>💡 Kerakli bo'limni tanlash uchun quyidagi tugmalardan foydalaning.</i>\n"
            f"<i>Ortga qaytish: «◀️ Asosiy menyu»</i>"
        )
        await message.answer(text, reply_markup=reply_kb)
        return

    text = (
        f"👑 <b>Alpha English Center — Boshqaruv Markazi (v2.7)</b>\n\n"
        f"Assalomu alaykum, <b>{user_name}</b>!\n"
        f"Tizimning barcha boshqaruv vositalari va yangi imkoniyatlari faollashtirildi:\n\n"
        f"▫️ <b>👑 Adminlar va 👨‍🏫 O'qituvchilar:</b> Yangi admin va ustozlarni tayinlash (<code>/add_admin</code>, <code>/add_teacher</code>) hamda to'liq shtat boshqaruvi.\n"
        f"▫️ <b>🤖 AI Test Generator & Builder:</b> PDF fayldan sun'iy intellekt (Gemini) orqali matnli (passage), True/False, Bo'sh joyni to'ldirish va yozma testlarni avtomatik tuzish.\n"
        f"▫️ <b>📊 WebApp Pro Dashboard:</b> Kurslar, Guruhlar (🔗 Telegram chat va Zoom havolalari), real vaqt statistikasi va Excel (.CSV) moliya hisobotlari.\n"
        f"▫️ <b>💰 Kassa & ⚖️ Qaytarish (Refund):</b> To'lovlarni tasdiqlash, qatnashilgan darslar asosida avtomatik refund hisoblash va xavfsiz boshqaruv.\n"
        f"▫️ <b>👥 Davomat & 📋 Uy Vazifasi:</b> Dars davomatini belgilash va o'quvchilarga avtomatik bildirishnomali vazifalar yuklash.\n"
        f"▫️ <b>📢 Pro Broadcast:</b> Barcha o'quvchilar va guruhlarga tugmali ommaviy xabarnomalar yuborish.\n"
        f"▫️ <b>🎓 Sertifikat & ⚙️ Sozlamalar:</b> Bitiruvchilarga rasmiy PDF sertifikat generatsiya qilish va markaz kontaktlarini boshqarish.\n\n"
        f"<i>💡 Boshqaruvni boshlash uchun quyidagi menyu tugmalaridan birini tanlang yoki WebApp dashboardni oching.</i>\n"
        f"<i>Ortga qaytish uchun: «◀️ Asosiy menyu» tugmasini bosing.</i>"
    )

    await message.answer(text, reply_markup=reply_kb)


from aiogram.filters import Command, CommandObject
from sqlalchemy import select, update
from backend.database import async_session
from backend.models import User, RoleEnum, Group

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


# --- 👨‍🏫 O'QITUVCHILARNI BOSHQARISH BUYRUQLARI ---

@router.message(Command("teachers"))
@router.message(F.text == ADMIN_MENU_TEXTS["TEACHERS"])
async def list_teachers_cmd(message: Message):
    if not await is_admin_or_manager(message.from_user.id):
        await message.answer("⚠️ Bu buyruq faqat adminlar uchun.")
        return

    async with async_session() as session:
        res = await session.execute(
            select(User).where(User.role == RoleEnum.teacher).order_by(User.id.desc())
        )
        teachers = res.scalars().all()

    if not teachers:
        await message.answer(
            "👨‍🏫 <b>Hozircha tizimda o'qituvchilar yo'q.</b>\n\n"
            "Yangi o'qituvchi qo'shish uchun: <code>/add_teacher [ID] [Ism]</code>"
        )
        return

    text = f"👨‍🏫 <b>O'qituvchilar Ro'yxati ({len(teachers)} ta):</b>\n\n"
    for idx, t in enumerate(teachers, 1):
        uname = f"(@{t.username})" if t.username else ""
        phone = f"📱 {t.phone}" if t.phone else ""
        text += f"{idx}. <b>{t.full_name}</b> {uname}\n   🆔 ID: <code>{t.id}</code> | {phone}\n\n"

    text += "<i>O'qituvchi qo'shish: <code>/add_teacher [ID] [Ism]</code>\nO'chirish: <code>/remove_teacher [ID]</code></i>"
    await message.answer(text)


@router.message(Command("add_teacher"))
async def add_teacher_cmd(message: Message, command: CommandObject):
    if not await is_admin_or_manager(message.from_user.id):
        await message.answer("⚠️ Bu buyruq faqat adminlar uchun.")
        return

    if not command.args:
        await message.answer(
            "👨‍🏫 <b>O'qituvchi qo'shish formati:</b>\n\n"
            "<code>/add_teacher [TELEGRAM_ID] [Ism Familiya]</code>\n\n"
            "<i>Namuna:</i>\n"
            "<code>/add_teacher 123456789 Jasur Abdullayev</code>"
        )
        return

    parts = command.args.strip().split(maxsplit=1)
    if not parts[0].isdigit():
        await message.answer("⚠️ Telegram ID faqat raqamdan iborat bo'lishi kerak!")
        return

    target_id = int(parts[0])
    target_name = parts[1] if len(parts) > 1 else f"Teacher #{target_id}"

    async with async_session() as session:
        user = await session.get(User, target_id)
        if user:
            user.role = RoleEnum.teacher
            if len(parts) > 1:
                user.full_name = target_name
        else:
            user = User(
                id=target_id,
                full_name=target_name,
                role=RoleEnum.teacher,
                referral_code=f"TEACH{target_id % 10000}",
                is_active=True,
            )
            session.add(user)
        await session.commit()

    from main import bot
    try:
        await bot.send_message(
            target_id,
            "🎉 <b>Tabriklaymiz! Sizga English Center botida O'qituvchi (Teacher) huquqlari berildi!</b>\n\n"
            "Boshqaruv menyusini ochish uchun <b>/admin</b> buyrug'ini yuboring."
        )
    except Exception:
        pass

    await message.answer(
        f"✅ <b>Yangi o'qituvchi muvaffaqiyatli biriktirildi!</b>\n\n"
        f"👨‍🏫 <b>Ismi:</b> {target_name}\n"
        f"🆔 <b>Telegram ID:</b> <code>{target_id}</code>\n"
        f"📌 <b>Roli:</b> Teacher (O'qituvchi)"
    )


@router.message(Command("remove_teacher"))
async def remove_teacher_cmd(message: Message, command: CommandObject):
    if not await is_admin_or_manager(message.from_user.id):
        await message.answer("⚠️ Bu buyruq faqat adminlar uchun.")
        return

    if not command.args or not command.args.strip().isdigit():
        await message.answer("⚠️ Format: <code>/remove_teacher [TELEGRAM_ID]</code>")
        return

    target_id = int(command.args.strip())
    async with async_session() as session:
        user = await session.get(User, target_id)
        if not user or user.role != RoleEnum.teacher:
            await message.answer("⚠️ Bu ID ga ega o'qituvchi topilmadi.")
            return

        user.role = RoleEnum.student
        await session.execute(
            update(Group).where(Group.teacher_id == target_id).values(teacher_id=None)
        )
        await session.commit()

    await message.answer(f"✅ O'qituvchi (ID: <code>{target_id}</code>) o'quvchi roliga o'tkazildi.")


@router.message(Command("admins"))
@router.message(F.text == ADMIN_MENU_TEXTS["ADMINS"])
async def list_admins_cmd(message: Message):
    if not await is_admin_or_manager(message.from_user.id):
        await message.answer("⚠️ Bu buyruq faqat bosh adminlar uchun.")
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                User.role.in_([RoleEnum.admin, RoleEnum.manager]),
                User.is_active == True,
            )
        )
        admins = result.scalars().all()

    text = f"👑 <b>Adminlar va Menejerlar Ro'yxati ({len(admins)} ta):</b>\n\n"
    for idx, a in enumerate(admins, 1):
        uname = f"(@{a.username})" if a.username else ""
        phone = f"📱 {a.phone}" if a.phone else ""
        text += f"{idx}. <b>{a.full_name}</b> {uname}\n   🆔 ID: <code>{a.id}</code> | {phone} | <i>{a.role.value}</i>\n\n"

    text += (
        "<i>Admin qo'shish: <code>/add_admin [TELEGRAM_ID] [Ism Familiya]</code>\n"
        "O'chirish: <code>/remove_admin [TELEGRAM_ID]</code>\n"
        "Yoki .env fayliga ADMINS=id1,id2 qo'shishingiz mumkin.</i>"
    )
    await message.answer(text)


@router.message(Command("add_admin"))
async def add_admin_cmd(message: Message, command: CommandObject):
    if not await is_admin_or_manager(message.from_user.id):
        await message.answer("⚠️ Bu buyruq faqat bosh adminlar uchun.")
        return

    if not command.args:
        await message.answer(
            "👑 <b>Admin qo'shish formati:</b>\n\n"
            "<code>/add_admin [TELEGRAM_ID] [Ism Familiya]</code>\n\n"
            "<i>Namuna:</i>\n"
            "<code>/add_admin 123456789 Jasur Admin</code>"
        )
        return

    parts = command.args.strip().split(maxsplit=1)
    if not parts[0].isdigit():
        await message.answer("⚠️ Telegram ID faqat raqamdan iborat bo'lishi kerak!")
        return

    target_id = int(parts[0])
    target_name = parts[1] if len(parts) > 1 else f"Admin #{target_id}"

    user = await add_admin(target_id, target_name)

    from main import bot
    try:
        await bot.send_message(
            target_id,
            "🎉 <b>Tabriklaymiz! Sizga English Center botida Administrator (Admin) huquqlari berildi!</b>\n\n"
            "Boshqaruv menyusini ochish uchun <b>/admin</b> buyrug'ini yuboring."
        )
    except Exception:
        pass

    await message.answer(
        f"✅ <b>Yangi admin muvaffaqiyatli tayinlandi!</b>\n\n"
        f"👑 <b>Ismi:</b> {user.full_name}\n"
        f"🆔 <b>Telegram ID:</b> <code>{user.id}</code>\n"
        f"📌 <b>Roli:</b> Admin (Boshqaruvchi)"
    )


@router.message(Command("remove_admin"))
async def remove_admin_cmd(message: Message, command: CommandObject):
    if not await is_admin_or_manager(message.from_user.id):
        await message.answer("⚠️ Bu buyruq faqat bosh adminlar uchun.")
        return

    if not command.args or not command.args.strip().isdigit():
        await message.answer("⚠️ Format: <code>/remove_admin [TELEGRAM_ID]</code>")
        return

    target_id = int(command.args.strip())
    if target_id == message.from_user.id:
        await message.answer("⚠️ O'zingizdan admin huquqini olib tashlay olmaysiz.")
        return

    async with async_session() as session:
        user = await session.get(User, target_id)
        if not user or user.role not in (RoleEnum.admin, RoleEnum.manager):
            await message.answer("⚠️ Bu ID ga ega admin topilmadi.")
            return

    await remove_admin(target_id)
    await message.answer(f"✅ Admin (ID: <code>{target_id}</code>) o'quvchi roliga o'tkazildi.")
