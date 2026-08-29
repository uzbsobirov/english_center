import asyncio
from sqlalchemy import select, delete

from backend.database import async_session
from backend.models import (
    User, RoleEnum, Group, Course, Payment, PaymentMethodEnum, PaymentStatusEnum,
    Enrollment, LevelEnum,
)
from backend.api.routes.admin import (
    get_admin_dashboard, get_admin_groups, get_admin_students, get_admin_payments,
    approve_admin_payment, broadcast_message, BroadcastPayload
)

async def run_admin_api_tests():
    print("--- [TEST] Running Stage 5 Admin API Test Suite ---")

    admin_id = 999000111
    student_id = 999000222
    admin_user = {"id": admin_id, "role": "admin"}

    async with async_session() as session:
        # Clean
        await session.execute(delete(Payment).where(Payment.student_id == student_id))
        await session.execute(delete(Enrollment).where(Enrollment.student_id == student_id))
        await session.execute(delete(User).where(User.id.in_([admin_id, student_id])))
        await session.commit()

        admin = User(id=admin_id, full_name="Super Admin", role=RoleEnum.admin)
        student = User(id=student_id, full_name="Student Test", role=RoleEnum.student)
        session.add_all([admin, student])

        # Get course & group
        course_res = await session.execute(select(Course).limit(1))
        course = course_res.scalars().first()
        group_res = await session.execute(select(Group).where(Group.course_id == course.id).limit(1))
        group = group_res.scalars().first()

        # Create pending payment
        payment = Payment(
            student_id=student_id,
            group_id=group.id,
            amount=500000.0,
            discount_amount=0.0,
            method=PaymentMethodEnum.cash,
            status=PaymentStatusEnum.pending,
        )
        session.add(payment)
        await session.commit()
        payment_id = payment.id

    # 1. Test Dashboard
    dashboard_data = await get_admin_dashboard(user=admin_user)
    assert "total_students" in dashboard_data
    assert "active_groups" in dashboard_data
    assert "total_revenue" in dashboard_data
    print(f"[OK] get_admin_dashboard: Students={dashboard_data['total_students']}, Revenue={dashboard_data['total_revenue']}")

    # 2. Test Groups
    groups_list = await get_admin_groups(user=admin_user)
    assert len(groups_list) > 0
    print(f"[OK] get_admin_groups: Found {len(groups_list)} groups")

    # 3. Test Students
    students_list = await get_admin_students(user=admin_user)
    assert len(students_list) > 0
    print(f"[OK] get_admin_students: Found {len(students_list)} students")

    # 4. Test Payments
    payments_list = await get_admin_payments(user=admin_user)
    assert len(payments_list) > 0
    print(f"[OK] get_admin_payments: Found {len(payments_list)} payments")

    # 5. Test Approve Payment
    approve_res = await approve_admin_payment(payment_id=payment_id, user=admin_user)
    assert approve_res["status"] == "success"
    print(f"[OK] approve_admin_payment: {approve_res['message']}")

    # 6. Test Broadcast
    broadcast_res = await broadcast_message(
        payload=BroadcastPayload(text="Test broadcast message", target_role="all"),
        user=admin_user,
    )
    assert broadcast_res["status"] == "success"
    print(f"[OK] broadcast_message: Total target={broadcast_res['total_target']}")

    # Cleanup
    async with async_session() as session:
        await session.execute(delete(Payment).where(Payment.student_id == student_id))
        await session.execute(delete(Enrollment).where(Enrollment.student_id == student_id))
        await session.execute(delete(User).where(User.id.in_([admin_id, student_id])))
        await session.commit()
        print("[OK] Test database cleaned up.")

    from main import bot
    try:
        await bot.session.close()
    except Exception:
        pass

    print("--- [ALL STAGE 5 ADMIN API TESTS PASSED] ---")


if __name__ == "__main__":
    asyncio.run(run_admin_api_tests())
