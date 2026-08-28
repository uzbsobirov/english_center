"""
Admin Web App API'si (TZ v2.6, 8-bo'lim).
- Dashboard statistikasi
- Barcha to'lovlar va qarzdorlar
- Broadcast yuborish
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func

from backend.database import async_session
from backend.models import Payment, PaymentStatusEnum, User, RoleEnum, Group, Course, Enrollment
from backend.deps import get_current_telegram_user
from backend.services.user_service import is_admin_or_manager

router = APIRouter(prefix="/api/admin", tags=["admin"])


class BroadcastPayload(BaseModel):
    text: str
    target_role: str | None = None  # student / teacher / all
    level: str | None = None


@router.get("/dashboard")
async def get_admin_dashboard(user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        total_students_res = await session.execute(
            select(func.count(User.id)).where(User.role == RoleEnum.student)
        )
        total_students = total_students_res.scalar() or 0

        active_groups_res = await session.execute(
            select(func.count(Group.id)).where(Group.is_active == True)
        )
        active_groups = active_groups_res.scalar() or 0

        payments_sum_res = await session.execute(
            select(func.sum(Payment.amount)).where(Payment.status == PaymentStatusEnum.confirmed)
        )
        total_revenue = float(payments_sum_res.scalar() or 0)

        pending_payments_res = await session.execute(
            select(func.count(Payment.id)).where(Payment.status == PaymentStatusEnum.pending)
        )
        pending_payments = pending_payments_res.scalar() or 0

    return {
        "total_students": total_students,
        "active_groups": active_groups,
        "total_revenue": total_revenue,
        "pending_payments": pending_payments,
    }


@router.post("/broadcast")
async def broadcast_message(
    payload: BroadcastPayload,
    user: dict = Depends(get_current_telegram_user),
):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        query = select(User.id).where(User.is_active == True)
        if payload.target_role and payload.target_role != "all":
            query = query.where(User.role == RoleEnum(payload.target_role))
        if payload.level:
            query = query.where(User.level == payload.level)

        res = await session.execute(query)
        user_ids = res.scalars().all()

    from main import bot
    sent_count = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, payload.text)
            sent_count += 1
        except Exception:
            continue

    return {"status": "success", "sent_count": sent_count, "total_target": len(user_ids)}
