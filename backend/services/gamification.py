"""
Gamification va Badge xizmati (TZ v2.6, 15-bo'lim).
- 🏅 Starter (1-testni ishlash)
- ⭐ Top Student (3 ta testda 90%+)
- 📅 Regular (10 ta darsga faol qatnashish)
- 👥 Ambassador (1 do'st taklif qilib, u to'lov qilganda)
- 🎯 Level Up (Keyingi daraja testini topshirish)
- 📝 Diligent (5 ta uy vazifasini o'z vaqtida topshirish)
- 🎓 Graduate (Kursni to'liq tugatish)
"""
from datetime import datetime
from sqlalchemy import select, func

from backend.database import async_session
from backend.models import UserBadge, TestResult, Attendance, AttendanceStatusEnum

BADGE_INFO = {
    "starter": {"name": "Starter", "icon": "🏅", "desc": "Birinchi testni muvaffaqiyatli ishlagan"},
    "top_student": {"name": "Top Student", "icon": "⭐", "desc": "3 ta testda 90%+ ball olgan"},
    "regular": {"name": "Regular", "icon": "📅", "desc": "10 ta darsga faol qatnashgan"},
    "ambassador": {"name": "Ambassador", "icon": "👥", "desc": "Do'stini taklif qilib, u kursga yozilgan"},
    "level_up": {"name": "Level Up", "icon": "🎯", "desc": "Yuqori daraja testini muvaffaqiyatli topshirgan"},
    "diligent": {"name": "Diligent", "icon": "📝", "desc": "5 ta uy vazifasini o'z vaqtida bajargan"},
    "graduate": {"name": "Graduate", "icon": "🎓", "desc": "Kursni to'liq va a'lo darajada tugatgan"},
}


async def award_badge_if_eligible(user_id: int, badge_type: str) -> bool:
    """Badge berilmagan bo'lsa, foydalanuvchiga beradi."""
    if badge_type not in BADGE_INFO:
        return False

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

    passed_tests = [r for r in results if r.passed]
    if len(passed_tests) >= 2:
        await award_badge_if_eligible(user_id, "level_up")


async def get_user_badges_summary(user_id: int) -> list[str]:
    """Foydalanuvchining barcha qo'lga kiritgan badge'larini ro'yxat ko'rinishida qaytaradi."""
    async with async_session() as session:
        res = await session.execute(
            select(UserBadge).where(UserBadge.user_id == user_id).order_by(UserBadge.earned_at.asc())
        )
        badges = res.scalars().all()

    result = []
    for b in badges:
        info = BADGE_INFO.get(b.badge_type, {"name": b.badge_type, "icon": "🎖"})
        result.append(f"{info['icon']} {info['name']}")
    return result
