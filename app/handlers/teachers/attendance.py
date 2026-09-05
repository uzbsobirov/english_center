"""
Davomat qo'yish (TZ v2.6, 7.3-bo'lim & 15 Gamification).
- Guruhni tanlash (O'qituvchi o'z guruhini, Admin barcha guruhlarni ko'ra oladi)
- Har bir o'quvchi uchun: Keldi ✅ / Kelmadi ❌ / Kech qoldi ⏰
- Kelmagan o'quvchiga avtomatik bildirishnoma ketadi
- 10 ta darsga ketma-ket/faol qatnashgan o'quvchiga 📅 Regular badge beriladi
"""
from datetime import date, datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, func

from backend.database import async_session
from backend.models import (
    Group, Enrollment, User, RoleEnum, Attendance, AttendanceStatusEnum, Course,
)
from backend.services.gamification import award_badge_if_eligible

router = Router()


async def _is_teacher_or_admin(telegram_id: int) -> bool:
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        return user is not None and user.role in (RoleEnum.teacher, RoleEnum.admin, RoleEnum.manager)


async def _get_groups_for_attendance(user_id: int):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user and user.role in (RoleEnum.admin, RoleEnum.manager):
            result = await session.execute(
                select(Group).where(Group.is_active == True)
            )
        else:
            result = await session.execute(
                select(Group).where(Group.teacher_id == user_id, Group.is_active == True)
            )
        return result.scalars().all()


from app.keyboards.admin_menu import ALL_ATTENDANCE_BUTTONS


@router.message(Command("attendance"))
@router.message(F.text.in_(ALL_ATTENDANCE_BUTTONS))
async def start_attendance(message: Message):
    if not await _is_teacher_or_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat o'qituvchilar va adminlar uchun.")
        return

    groups = await _get_groups_for_attendance(message.from_user.id)
    if not groups:
        await message.answer("Sizga biriktirilgan faol guruh topilmadi.")
        return

    buttons = [
        [InlineKeyboardButton(text=f"👥 {g.name}", callback_data=f"att_group:{g.id}")]
        for g in groups
    ]
    buttons.append([InlineKeyboardButton(text="🎯 Sinov darslari davomati (Free Trial)", callback_data="show_trial_attendance_list")])
    await message.answer(
        "📋 <b>Dars Davomati</b>\n\nDavomat olmoqchi bo'lgan guruhingizni tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("att_group:"))
async def attendance_group_selected(callback: CallbackQuery):
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

    first_student = students[0]
    keyboard = _build_attendance_keyboard(group_id, first_student.id, 0, len(students))
    await callback.message.edit_text(
        f"📋 <b>{group.name} guruhi davomati</b>\n"
        f"📅 Sana: <b>{date.today().strftime('%d.%m.%Y')}</b>\n\n"
        f"👤 O'quvchi (1/{len(students)}): <b>{first_student.full_name}</b>\n\n"
        f"Statusni belgilang:",
        reply_markup=keyboard,
    )
    await callback.answer()


def _build_attendance_keyboard(group_id: int, student_id: int, index: int, total: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Keldi ✅", callback_data=f"att_mark:{group_id}:{student_id}:{index}:{total}:present"),
            InlineKeyboardButton(text="Kelmadi ❌", callback_data=f"att_mark:{group_id}:{student_id}:{index}:{total}:absent"),
            InlineKeyboardButton(text="Kech qoldi ⏰", callback_data=f"att_mark:{group_id}:{student_id}:{index}:{total}:late"),
        ]
    ])


@router.callback_query(F.data.startswith("att_mark:"))
async def mark_student_attendance(callback: CallbackQuery):
    parts = callback.data.split(":")
    group_id = int(parts[1])
    student_id = int(parts[2])
    index = int(parts[3])
    total = int(parts[4])
    status_str = parts[5]

    status_enum = AttendanceStatusEnum(status_str)
    teacher_id = callback.from_user.id
    awarded_regular_badge = False

    async with async_session() as session:
        # Bugungi kun uchun oldingi belgilanishni tekshiramiz
        existing = await session.execute(
            select(Attendance).where(
                Attendance.group_id == group_id,
                Attendance.student_id == student_id,
                Attendance.lesson_date == date.today(),
            )
        )
        existing_att = existing.scalar_one_or_none()
        if existing_att:
            existing_att.status = status_enum
            existing_att.marked_by = teacher_id
        else:
            att = Attendance(
                group_id=group_id,
                student_id=student_id,
                lesson_date=date.today(),
                status=status_enum,
                marked_by=teacher_id,
            )
            session.add(att)

        group = await session.get(Group, group_id)

        # Gamification: 10 ta dars qatnashuvi tekshiruvi (TZ 15)
        if status_enum in (AttendanceStatusEnum.present, AttendanceStatusEnum.late):
            att_count_res = await session.execute(
                select(func.count(Attendance.id)).where(
                    Attendance.student_id == student_id,
                    Attendance.status.in_([AttendanceStatusEnum.present, AttendanceStatusEnum.late]),
                )
            )
            total_attended = att_count_res.scalar() or 0
            if total_attended >= 10:
                awarded_regular_badge = await award_badge_if_eligible(student_id, "regular")

        await session.commit()

        # O'quvchilar ro'yxatini qayta yuklash
        enrolled_res = await session.execute(
            select(User)
            .join(Enrollment, Enrollment.student_id == User.id)
            .where(Enrollment.group_id == group_id, Enrollment.is_active == True)
        )
        students = enrolled_res.scalars().all()

    from main import bot

    # Agar kelmagan bo'lsa o'quvchiga avtomatik xabarnoma (TZ 13)
    if status_enum == AttendanceStatusEnum.absent:
        try:
            await bot.send_message(
                student_id,
                f"⚠️ <b>Bugun {group.name if group else 'kurs'} darsida bo'lmadingiz.</b>\n\n"
                f"O'tilgan mavzular va yangi topshiriqlarni «📋 Uy Vazifam» bo'limidan tekshirib oling! 📚",
            )
        except Exception:
            pass

    # Agar Regular badge olgan bo'lsa tabriklash
    if awarded_regular_badge:
        try:
            await bot.send_message(
                student_id,
                f"🎉 <b>Tabriklaymiz!</b>\n\n"
                f"Siz 10 ta darsga faol qatnashib, 📅 <b>Regular badge</b> mukofotini qo'lga kiritdingiz! 🌟",
            )
        except Exception:
            pass

    # Keyingi o'quvchi
    next_index = index + 1
    if next_index >= len(students):
        await callback.message.edit_text(
            f"✅ <b>{group.name if group else 'Guruh'} davomati to'liq yakunlandi va saqlandi!</b>\n"
            f"📅 Sana: <b>{date.today().strftime('%d.%m.%Y')}</b>"
        )
        await callback.answer("Davomat yakunlandi!")
        return

    next_student = students[next_index]
    keyboard = _build_attendance_keyboard(group_id, next_student.id, next_index, len(students))
    await callback.message.edit_text(
        f"📋 <b>{group.name if group else 'Guruh'} davomati</b> ({next_index + 1}/{len(students)})\n"
        f"📅 Sana: <b>{date.today().strftime('%d.%m.%Y')}</b>\n\n"
        f"👤 O'quvchi: <b>{next_student.full_name}</b>\n\n"
        f"Statusni belgilang:",
        reply_markup=keyboard,
    )
    await callback.answer()
