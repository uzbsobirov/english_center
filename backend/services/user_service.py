"""
Foydalanuvchi rollari va boshqaruvi bo'yicha xizmatlar.
TZ v2.6, 18-bo'lim: Admin/Manager IDlari qattiq kodlanmaydi, bazadan dinamik olinadi.
"""
from sqlalchemy import select
from backend.database import async_session
from backend.models import User, RoleEnum
from data.config import ADMINS, DEV_MODE


async def get_admin_ids() -> list[int]:
    """Barcha faol adminlar va menejerlarning Telegram ID larini qaytaradi."""
    async with async_session() as session:
        result = await session.execute(
            select(User.id).where(
                User.role.in_([RoleEnum.admin, RoleEnum.manager]),
                User.is_active == True,
            )
        )
        db_admin_ids = [int(uid) for uid in result.scalars().all()]

    env_admin_ids = [int(a) for a in ADMINS if str(a).strip().isdigit()]
    return list(set(db_admin_ids + env_admin_ids))


async def get_teacher_ids(level: str | None = None) -> list[int]:
    """O'qituvchilarning Telegram ID larini qaytaradi."""
    async with async_session() as session:
        query = select(User.id).where(
            User.role == RoleEnum.teacher,
            User.is_active == True,
        )
        result = await session.execute(query)
        return [int(uid) for uid in result.scalars().all()]


async def is_admin_or_manager(telegram_id: int) -> bool:
    """Foydalanuvchi admin yoki manager ekanligini bazadan yoki .env dan tekshiradi."""
    if DEV_MODE and telegram_id == 999999999:
        return True

    env_admin_ids = [int(a) for a in ADMINS if str(a).strip().isdigit()]
    if telegram_id in env_admin_ids:
        return True

    async with async_session() as session:
        user = await session.get(User, telegram_id)
        if not user:
            return False
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        return role_val in ("admin", "manager", "super_admin") and user.is_active


async def is_teacher(telegram_id: int) -> bool:
    """Foydalanuvchi o'qituvchi ekanligini bazadan tekshiradi."""
    if DEV_MODE and telegram_id == 999999999:
        return True

    async with async_session() as session:
        user = await session.get(User, telegram_id)
        if not user:
            return False
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        return role_val in ("teacher", "admin", "manager") and user.is_active
