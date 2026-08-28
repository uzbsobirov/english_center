"""
🏆 Reyting bo'limi (TZ v2.6, 6.3 va 15-bo'lim).
- Guruh yoki markaz bo'yicha TOP-10 o'quvchilar
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
    async with async_session() as session:
        # Eng yuqori ball to'plagan 10 ta test natijasini olamiz
        result = await session.execute(
            select(TestResult, User)
            .join(User, TestResult.student_id == User.id)
            .order_by(desc(TestResult.percent))
            .limit(10)
        )
        top_records = result.all()

    if not top_records:
        await message.answer("🏆 Hozircha reyting ma'lumotlari mavjud emas.")
        return

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = ["🏆 <b>Markaz TOP-10 O'quvchilari Reytingi:</b>\n"]

    for idx, (tr, user) in enumerate(top_records):
        badge = medals[idx] if idx < len(medals) else "▫️"
        text.append(
            f"{badge} <b>{user.full_name}</b> — <b>{tr.percent:.1f}%</b> ({tr.score} ball)"
        )

    await message.answer("\n".join(text))
