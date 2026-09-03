"""
📊 O'quvchi Progress va Natijalari bo'limi (TZ v2.6, 11 & 15-bo'limlar).
- Davomat foizi (Attendance %)
- Test natijalari va o'rtacha ball
- Gamifikatsiya (Badge'lar va unvonlar)
- Uy vazifalari bajarilishi
- Web App Mini App orqali grafikli ko'rinish
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram_i18n import I18nContext
from sqlalchemy import select, func

from backend.database import async_session
from backend.models import (
    User, Attendance, AttendanceStatusEnum, TestResult,
    Homework, Enrollment, Group, Course
)
from backend.services.gamification import get_user_badges_summary
from data.config import env

router = Router()

WEBAPP_URL = env.str("WEBAPP_URL", "https://t.me")

PROGRESS_BUTTON_TEXTS = {
    "📊 Progress", "📊 Прогресс", "📊 Statistika",
    "Progress", "Прогресс", "Statistika",
}


@router.message(Command("progress"))
@router.message(F.text.in_(PROGRESS_BUTTON_TEXTS))
async def show_student_progress(message: Message, i18n: I18nContext):
    user_id = message.from_user.id

    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            user = User(
                id=user_id,
                full_name=message.from_user.full_name or "O'quvchi",
                username=message.from_user.username,
            )
            session.add(user)
            await session.commit()

        # 1. Faol guruh
        enr_res = await session.execute(
            select(Enrollment, Group, Course)
            .join(Group, Enrollment.group_id == Group.id)
            .join(Course, Group.course_id == Course.id)
            .where(
                Enrollment.student_id == user_id,
                Enrollment.is_active == True,
            ).limit(1)
        )
        enr_data = enr_res.first()

        # 2. Davomat hisobi
        total_att_res = await session.execute(
            select(func.count(Attendance.id)).where(Attendance.student_id == user_id)
        )
        total_att = total_att_res.scalar() or 0

        present_att_res = await session.execute(
            select(func.count(Attendance.id)).where(
                Attendance.student_id == user_id,
                Attendance.status.in_([AttendanceStatusEnum.present, AttendanceStatusEnum.late]),
            )
        )
        present_att = present_att_res.scalar() or 0
        att_pct = (present_att / total_att * 100) if total_att > 0 else 100.0

        # 3. Test natijalari
        tests_res = await session.execute(
            select(TestResult).where(TestResult.student_id == user_id).order_by(TestResult.created_at.desc())
        )
        tests = tests_res.scalars().all()
        avg_test = (sum(float(t.percent) for t in tests) / len(tests)) if tests else 0.0

        # 4. Badges
        badges = await get_user_badges_summary(user_id)

    # Progress bar generatsiyasi (masalan: [🟩🟩🟩🟩⬜️⬜️⬜️⬜️⬜️⬜️] 40%)
    filled_blocks = min(10, int(att_pct / 10))
    bar = "🟩" * filled_blocks + "⬜️" * (10 - filled_blocks)
    badges_text = " • ".join(badges) if badges else "Boshlang'ich"

    group_name = enr_data[1].name if enr_data else "Guruhga yozilmagan"
    course_name = enr_data[2].title.get("uz", "Ingliz tili") if enr_data and isinstance(enr_data[2].title, dict) else (enr_data[2].title if enr_data else "-")

    text = (
        f"📊 <b>Sizning O'quv Progressingiz</b>\n\n"
        f"👤 <b>O'quvchi:</b> {message.from_user.full_name}\n"
        f"📚 <b>Guruh:</b> {group_name} ({course_name})\n\n"
        f"📈 <b>Davomat intizomi:</b>\n"
        f"[{bar}] <b>{att_pct:.1f}%</b> ({present_att}/{total_att} dars)\n\n"
        f"📝 <b>Testlar natijasi:</b>\n"
        f"▫️ Topshirilgan testlar: <b>{len(tests)} ta</b>\n"
        f"▫️ O'rtacha o'zlashtirish: <b>{avg_test:.1f}%</b>\n\n"
        f"🏅 <b>Yutuqlar va Badge'lar:</b>\n"
        f"{badges_text}"
    )

    keyboard_buttons = []
    # WebApp URL bo'lsa grafikli tahlil tugmasi
    if WEBAPP_URL.startswith("https://"):
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="📱 Batafsil grafiklar (Web App)",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}/progress"),
            )
        ])

    await message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons) if keyboard_buttons else None,
    )
