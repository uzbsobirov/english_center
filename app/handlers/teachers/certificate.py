"""
Sertifikat berish (TZ v2.6, 17-bo'lim & 15 Gamification).
- O'qituvchi yoki Admin `/issue_certificate` komandasi orqali guruh o'quvchisiga rasmiy PDF sertifikat beradi.
- ReportLab orqali IELTS / CEFR formatida PDF generatsiya qilinadi va o'quvchiga Telegram Document sifatida yuboriladi.
- O'quvchiga 'Graduate' badge beriladi.
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from sqlalchemy import select

from backend.database import async_session
from backend.models import Group, Course, Enrollment, User, RoleEnum
from backend.services.certificate_generator import generate_certificate_pdf
from backend.services.gamification import award_badge_if_eligible

router = Router()


async def _is_teacher_or_admin(telegram_id: int) -> bool:
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        return user is not None and user.role in (RoleEnum.teacher, RoleEnum.admin, RoleEnum.manager)


async def _get_groups(user_id: int):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user and user.role in (RoleEnum.admin, RoleEnum.manager):
            result = await session.execute(select(Group).where(Group.is_active == True))
        else:
            result = await session.execute(select(Group).where(Group.teacher_id == user_id, Group.is_active == True))
        return result.scalars().all()


@router.message(Command("issue_certificate"))
@router.message(F.text.in_({"🎓 Sertifikat berish", "🎓 Sertifikat", "Sertifikat berish", "Certificate"}))
async def start_issue_certificate(message: Message):
    if not await _is_teacher_or_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat o'qituvchilar va adminlar uchun.")
        return

    groups = await _get_groups(message.from_user.id)
    if not groups:
        await message.answer("Faol guruhlar topilmadi.")
        return

    buttons = [
        [InlineKeyboardButton(text=f"👥 {g.name}", callback_data=f"cert_group:{g.id}")]
        for g in groups
    ]
    await message.answer(
        "🎓 <b>Sertifikat Berish</b>\n\nQaysi guruh o'quvchisiga sertifikat bermoqchisiz?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("cert_group:"))
async def cert_group_selected(callback: CallbackQuery):
    group_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        group = await session.get(Group, group_id)
        enrolled_res = await session.execute(
            select(User)
            .join(Enrollment, Enrollment.student_id == User.id)
            .where(Enrollment.group_id == group_id, Enrollment.is_active == True)
        )
        students = enrolled_res.scalars().all()

    if not students:
        await callback.message.edit_text(f"👥 <b>{group.name}</b> guruhida hozircha o'quvchilar yo'q.")
        await callback.answer()
        return

    buttons = [
        [InlineKeyboardButton(text=f"👤 {s.full_name}", callback_data=f"cert_student:{group_id}:{s.id}")]
        for s in students
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="cert_back_groups")])

    await callback.message.edit_text(
        f"👥 <b>{group.name}</b> guruhi o'quvchilari:\n\nSertifikat beriladigan o'quvchini tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data == "cert_back_groups")
async def cert_back_to_groups(callback: CallbackQuery):
    groups = await _get_groups(callback.from_user.id)
    buttons = [
        [InlineKeyboardButton(text=f"👥 {g.name}", callback_data=f"cert_group:{g.id}")]
        for g in groups
    ]
    await callback.message.edit_text(
        "🎓 <b>Sertifikat Berish</b>\n\nGuruhni tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cert_student:"))
async def cert_issue_process(callback: CallbackQuery):
    parts = callback.data.split(":")
    group_id = int(parts[1])
    student_id = int(parts[2])

    await callback.message.edit_text("⏳ <i>PDF sertifikat generatsiya qilinmoqda...</i>")

    async with async_session() as session:
        group = await session.get(Group, group_id)
        course = await session.get(Course, group.course_id)
        student = await session.get(User, student_id)

    if not student or not group or not course:
        await callback.message.edit_text("Ma'lumotlar topilmadi.")
        return

    course_name = course.title.get("en", "General English") if isinstance(course.title, dict) else str(course.title)
    level_name = course.level.value if hasattr(course.level, "value") else str(course.level)

    pdf_bytes = generate_certificate_pdf(
        student_name=student.full_name,
        course_type=course_name,
        level=level_name,
    )

    from main import bot

    doc = BufferedInputFile(pdf_bytes, filename=f"Certificate_{student.full_name.replace(' ', '_')}.pdf")

    # 1. O'quvchiga sertifikatni yuborish
    try:
        await award_badge_if_eligible(student_id, "graduate")
        await bot.send_document(
            student_id,
            doc,
            caption=(
                f"🎓 <b>Tabriklaymiz, {student.full_name}!</b>\n\n"
                f"Siz <b>{group.name}</b> guruhidagi <b>{course_name} ({level_name})</b> kursini muvaffaqiyatli yakunladingiz!\n\n"
                f"Sizning rasmiy sertifikatingiz tayyorlandi. Kelgusi faoliyatingizda ulkan zafarlar tilaymiz! 🌟\n"
                f"<i>(Sizga 🎓 Graduate badge berildi)</i>"
            ),
        )
    except Exception as e:
        await callback.message.edit_text(f"⚠️ O'quvchiga yuborishda xatolik: {e}")
        return

    # 2. O'qituvchiga ham nusxasini ko'rsatish
    teacher_doc = BufferedInputFile(pdf_bytes, filename=f"Certificate_{student.full_name.replace(' ', '_')}.pdf")
    await callback.message.answer_document(
        teacher_doc,
        caption=f"✅ <b>{student.full_name}</b> uchun sertifikat tayyorlandi va uning Telegram botiga yuborildi!",
    )
    await callback.message.delete()
