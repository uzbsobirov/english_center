import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, delete, update
from backend.database import async_session
from backend.models import (
    User, Enrollment, Payment, Attendance, FreeTrialRequest,
    Refund, WaitingList, GroupChangeRequest, ReferralBonus,
    TestResult, SupportChat, UserBadge, Group
)

async def delete_user(target_id: int):
    async with async_session() as session:
        user = await session.get(User, target_id)
        if not user:
            print(f"[-] User {target_id} bazada topilmadi.")
            return

        print(f"[*] User {target_id} ({user.full_name}, role: {user.role}) ma'lumotlari o'chirilmoqda...")

        # 1. Foreign key references in other tables
        await session.execute(update(Group).where(Group.teacher_id == target_id).values(teacher_id=None))
        await session.execute(update(User).where(User.referred_by == target_id).values(referred_by=None))

        # 2. Delete child records
        await session.execute(delete(Attendance).where(
            (Attendance.student_id == target_id) | (Attendance.marked_by == target_id)
        ))
        await session.execute(delete(Enrollment).where(Enrollment.student_id == target_id))
        await session.execute(delete(Payment).where(
            (Payment.student_id == target_id) | (Payment.confirmed_by == target_id)
        ))
        await session.execute(delete(FreeTrialRequest).where(
            (FreeTrialRequest.student_id == target_id) | (FreeTrialRequest.teacher_id == target_id)
        ))
        await session.execute(delete(Refund).where(
            (Refund.student_id == target_id) | (Refund.approved_by == target_id)
        ))
        await session.execute(delete(WaitingList).where(WaitingList.student_id == target_id))
        await session.execute(delete(GroupChangeRequest).where(
            (GroupChangeRequest.student_id == target_id) | (GroupChangeRequest.approved_by == target_id)
        ))
        await session.execute(delete(ReferralBonus).where(
            (ReferralBonus.user_id == target_id) | (ReferralBonus.referred_student_id == target_id)
        ))
        await session.execute(delete(TestResult).where(TestResult.student_id == target_id))
        await session.execute(delete(SupportChat).where(
            (SupportChat.student_id == target_id) | (SupportChat.admin_id == target_id)
        ))
        await session.execute(delete(UserBadge).where(UserBadge.user_id == target_id))

        # 3. Delete user
        await session.delete(user)
        await session.commit()
        print(f"[+] User {target_id} barcha ma'lumotlari bilan bazadan to'liq o'chirildi!")

if __name__ == "__main__":
    target = 7195359577
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        target = int(sys.argv[1])
    asyncio.run(delete_user(target))
