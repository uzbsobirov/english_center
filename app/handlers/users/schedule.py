"""
📅 Jadvalim bo'limi (TZ v2.6, 6.3 va 16-bo'lim).
- Guruhning haftalik dars jadvali, xona va Zoom havolasi
"""
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_i18n import I18nContext
from sqlalchemy import select

from backend.database import async_session
from backend.models import Enrollment, Group, Course

router = Router()

SCHEDULE_BUTTON_TEXTS = {"📅 Jadvalim", "📅 Расписание", "📅 My Schedule"}


@router.message(F.text.in_(SCHEDULE_BUTTON_TEXTS))
async def show_schedule(message: Message, i18n: I18nContext):
    user_id = message.from_user.id

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
                "📅 <b>Siz hali hech qaysi guruhga a'zo emassiz.</b>\n"
                "Jadvalni ko'rish uchun avval guruhga yoziling:",
                reply_markup=keyboard,
            )
            return

        group = await session.get(Group, enrollment.group_id)
        course = await session.get(Course, group.course_id) if group else None

    if not group:
        await message.answer("Guruh topilmadi.")
        return

    days_map = {1: "Dushanba", 2: "Seshanba", 3: "Chorshanba", 4: "Payshanba", 5: "Juma", 6: "Shanba", 7: "Yakshanba"}
    schedule_lines = []
    if group.schedule:
        for item in group.schedule:
            d_name = days_map.get(item.get("day"), f"{item.get('day')}-kun")
            t_name = item.get("time", "")
            schedule_lines.append(f"🗓 <b>{d_name}:</b> {t_name}")
    else:
        schedule_lines.append("<i>Jadval hali kiritilmagan.</i>")

    text = [
        f"📅 <b>Dars Jadvalingiz:</b>\n",
        f"👥 Guruh: <b>{group.name}</b>",
        f"📚 Kurs: <b>{course.level.value if course else ''}</b>",
        f"📍 Xona: <b>{group.room or 'Asosiy xona'}</b>\n",
        *schedule_lines
    ]

    buttons = []
    if group.zoom_link:
        buttons.append([InlineKeyboardButton(text="🌐 Zoom Online Dars Havolasi", url=group.zoom_link)])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
    await message.answer("\n".join(text), reply_markup=keyboard)
