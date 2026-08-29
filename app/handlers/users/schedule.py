"""
📅 Jadvalim bo'limi (TZ v2.6, 6.3 va 16-bo'lim).
- Guruhning haftalik dars jadvali, xona va Zoom havolasi
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_i18n import I18nContext
from sqlalchemy import select

from backend.database import async_session
from backend.models import Enrollment, Group, Course
from backend.utils.formatters import format_schedule

router = Router()

SCHEDULE_BUTTON_TEXTS = {
    "📅 Jadvalim", "📅 Расписание", "📅 My Schedule",
    "Jadvalim", "Расписание", "My Schedule", "Schedule",
}


@router.message(Command("schedule"))
@router.message(F.text.in_(SCHEDULE_BUTTON_TEXTS))
async def show_schedule(message: Message, i18n: I18nContext):
    user_id = message.from_user.id
    lang = getattr(i18n, "locale", "uz") or "uz"

    async with async_session() as session:
        enrollment_res = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == user_id,
                Enrollment.is_active == True,
            ).order_by(Enrollment.enrolled_at.desc())
        )
        enrollment = enrollment_res.scalar_one_or_none()

        if not enrollment:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📝 Free darsga yozilish", callback_data="start_free_trial_flow")]
            ])
            await message.answer(
                "📅 <b>Siz hali hech qaysi guruhga a'zo emassiz.</b>\n\n"
                "Dars jadvalini ko'rish uchun bepul sinov darsiga yoziling:",
                reply_markup=keyboard,
            )
            return

        group = await session.get(Group, enrollment.group_id)
        course = await session.get(Course, group.course_id) if group else None

    if not group:
        await message.answer("Guruh topilmadi.")
        return

    level_val = (course.level.value if hasattr(course.level, 'value') else str(course.level)) if course else ''
    course_title = (course.title.get(lang, course.title.get("uz", "")) if isinstance(course.title, dict) else str(course.title)) if course else ''
    sched_formatted = format_schedule(group.schedule, lang)

    text = [
        f"📅 <b>Dars Jadvalingiz:</b>\n",
        f"👥 Guruh: <b>{group.name}</b>",
        f"📚 Kurs: <b>{course_title} ({level_val})</b>" if course_title else f"📚 Daraja: <b>{level_val}</b>",
        f"🗓 Dars vaqti: <b>{sched_formatted}</b>",
        f"📍 Xona / Manzil: <b>{group.room or 'Asosiy xona'}</b>",
    ]

    buttons = []
    if group.zoom_link:
        buttons.append([InlineKeyboardButton(text="🌐 Zoom Online Dars Havolasi", url=group.zoom_link)])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
    await message.answer("\n".join(text), reply_markup=keyboard)
