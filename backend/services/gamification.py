"""
Gamification va Badge xizmati (TZ v2.6, 15-bo'lim).
- 🏅 Starter (1-testni ishlash)
- ⭐ Top Student (3 ta testda 90%+)
- 📅 Regular (10 ta darsga ketma-ket qatnashish)
- 👥 Ambassador (1 do'st taklif qilib, u to'lov qilganda)
- 🎯 Level Up (Keyingi daraja testini topshirish)
- 📝 Diligent (5 ta uy vazifasini o'z vaqtida topshirish)
- 🎓 Graduate (Kursni to'liq tugatish)
"""
from datetime import datetime
from sqlalchemy import select, func

from backend.database import async_session
from backend.models import UserBadge, TestResult, Attendance, ReferralBonus


async def award_badge_if_eligible(user_id: int, badge_type: str) -> bool:
    """Badge berilmagan bo'lsa, foydalanuvchiga beradi."""
    async with async_session() as session:
        existing = await session.execute(
            select(UserBadge).where(UserBadge.user_id == user_id, UserBadge.badge_type == badge_type)
        )
        if existing.scalar_one_or_none() is not None:
            return False  # Allaqachon olingan

        badge = UserBadge(user_id=user_id, badge_type=badge_type)
        session.add(badge)
        await session.commit()
        return True


async def check_test_badges(user_id: int):
    """Test topshirilgandan keyingi badge'larni tekshiradi."""
    async with async_session() as session:
        res = await session.execute(
            select(TestResult).where(TestResult.student_id == user_id)
        )
        results = res.scalars().all()

    if len(results) >= 1:
        await award_badge_if_eligible(user_id, "starter")

    high_scores = [r for r in results if float(r.percent) >= 90.0]
    if len(high_scores) >= 3:
        await award_badge_if_eligible(user_id, "top_student")
