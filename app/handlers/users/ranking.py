"""
🏆 Reyting bo'limi (TZ v2.6, 6.3 va 15-bo'lim).
- Markaz va guruh bo'yicha TOP-10 o'quvchilar
- Foydalanuvchining o'z o'rni
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram_i18n import I18nContext
from sqlalchemy import select, desc

from backend.database import async_session
from backend.models import TestResult, User

router = Router()

RANKING_BUTTON_TEXTS = {"🏆 Reyting", "🏆 Рейтинг", "🏆 Ranking"}


@router.message(F.text.in_(RANKING_BUTTON_TEXTS))
async def show_ranking(message: Message, i18n: I18nContext):
    user_id = message.from_user.id
    lang = getattr(i18n, "locale", "uz") or "uz"

    async with async_session() as session:
        # Eng yuqori ball to'plagan test natijalari
        result = await session.execute(
            select(TestResult, User)
            .join(User, TestResult.student_id == User.id)
            .order_by(desc(TestResult.percent), desc(TestResult.score))
            .limit(10)
        )
        top_records = result.all()

        # Joriy foydalanuvchining eng yaxshi natijasi
        user_best_res = await session.execute(
            select(TestResult)
            .where(TestResult.student_id == user_id)
            .order_by(desc(TestResult.percent))
            .limit(1)
        )
        user_best = user_best_res.scalar_one_or_none()

    if not top_records:
        no_data_msg = (
            "🏆 Hozircha reyting ma'lumotlari mavjud emas. Birinchi bo'lib test topshiring va TOP-1 ga chiqing!"
            if lang == "uz"
            else (
                "🏆 Данных рейтинга пока нет. Пройдите тест первым и станьте ТОП-1!"
                if lang == "ru"
                else "🏆 No ranking data available yet. Be the first to take a test and reach TOP-1!"
            )
        )
        await message.answer(no_data_msg)
        return

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    if lang == "uz":
        title = "🏆 <b>Alpha English Center — TOP-10 O'quvchilari</b>\n"
        personal_label = "📍 <b>Sizning eng yaxshi natijangiz:</b>"
    elif lang == "ru":
        title = "🏆 <b>Alpha English Center — ТОП-10 Студентов</b>\n"
        personal_label = "📍 <b>Ваш лучший результат:</b>"
    else:
        title = "🏆 <b>Alpha English Center — TOP-10 Students</b>\n"
        personal_label = "📍 <b>Your best result:</b>"

    text = [title]
    user_in_top = False

    for idx, (tr, u) in enumerate(top_records):
        badge = medals[idx] if idx < len(medals) else "▫️"
        is_current_user = u.id == user_id
        if is_current_user:
            user_in_top = True
            text.append(
                f"{badge} <b>{u.full_name} (Siz)</b> — <b>{tr.percent:.1f}%</b> ({tr.score} ball) ⭐"
            )
        else:
            text.append(
                f"{badge} <b>{u.full_name}</b> — <b>{tr.percent:.1f}%</b> ({tr.score} ball)"
            )

    if user_best and not user_in_top:
        text.append(f"\n{personal_label} <b>{user_best.percent:.1f}%</b> ({user_best.score} ball)")

    await message.answer("\n".join(text))
