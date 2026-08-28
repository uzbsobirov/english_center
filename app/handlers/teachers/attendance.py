"""
Davomat qo'yish (TZ v2.6, 7.3-bo'lim).
- Guruhni tanlash
- Har bir o'quvchi uchun: Keldi ✅ / Kelmadi ❌ / Kech qoldi ⏰
- Kelmagan o'quvchiga avtomatik bildirishnoma ketadi
"""
from datetime import date, datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from backend.database import async_session
from backend.models import Group, Enrollment, User, Attendance, AttendanceStatusEnum
from backend.services.user_service import is_teacher

router = Router()


@router.message(Command("attendance"))
async def start_attendance(message: Message):
    if not await is_teacher(message.from_user.id):
        await message.answer("Bu buyruq faqat o'qituvchilar uchun.")
        return

    async with async_session() as session:
        result = await session.execute(
            select(Group).where(Group.teacher_id == message.from_user.id, Group.is_active == True)
        )
        groups = result.scalars().all()

    if not groups:
        await message.answer("Sizga biriktirilgan faol guruh topilmadi.")
        return

    buttons = [
        [InlineKeyboardButton(text=g.name, callback_data=f"att_group:{g.id}")]
        for g in groups
    ]
    await message.answer("📋 Davomat qo'ymoqchi bo'lgan guruhingizni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


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
        await callback.message.edit_text(f"<b>{group.name}</b> guruhida hozircha o'quvchilar yo'q.")
        await callback.answer()
        return

    # 1-o'quvchini belgilashni boshlaymiz
    first_student = students[0]
    keyboard = _build_attendance_keyboard(group_id, first_student.id, 0, len(students))
    await callback.message.edit_text(
        f"📋 <b>{group.name} guruhi davomati</b>\n"
        f"📅 Sana: <b>{date.today().strftime('%d.%m.%Y')}</b>\n\n"
        f"👤 O'quvchi (1/{len(students)}): <b>{first_student.full_name}</b>\n\n"
        f"Statusni tanlang:",
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

    async with async_session() as session:
        att = Attendance(
            group_id=group_id,
            student_id=student_id,
            lesson_date=date.today(),
            status=status_enum,
            marked_by=teacher_id,
        )
        session.add(att)
        await session.commit()

        # Agar kelmagan bo'lsa o'quvchiga avtomatik xabar
        if status_enum == AttendanceStatusEnum.absent:
            from main import bot
            try:
                await bot.send_message(
                    student_id,
                    "⚠️ <b>Bugun darsda bo'lmadingiz.</b>\n"
                    "O'tilgan mavzular va uy vazifasini «📋 Uy Vazifam» bo'limidan tekshirib oling!"
                )
            except Exception:
                pass

        # Keyingi o'quvchini olamiz
        next_index = index + 1
        enrolled_res = await session.execute(
            select(User)
            .join(Enrollment, Enrollment.student_id == User.id)
            .where(Enrollment.group_id == group_id, Enrollment.is_active == True)
        )
        students = enrolled_res.scalars().all()

    if next_index >= len(students):
        await callback.message.edit_text("✅ <b>Guruh davomati to'liq belgilandi va saqlandi!</b>")
        await callback.answer("Davomat yakunlandi!")
        return

    next_student = students[next_index]
    keyboard = _build_attendance_keyboard(group_id, next_student.id, next_index, len(students))
    await callback.message.edit_text(
        f"📋 <b>Davomat davom etmoqda</b> ({next_index + 1}/{len(students)})\n\n"
        f"👤 O'quvchi: <b>{next_student.full_name}</b>\n\n"
        f"Statusni tanlang:",
        reply_markup=keyboard,
    )
    await callback.answer()
