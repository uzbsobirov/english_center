import sys
import asyncio
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.database import async_session
from backend.models import (
    User, RoleEnum, LanguageEnum, Group, Course,
    Enrollment, EnrollmentStatusEnum, Payment, PaymentStatusEnum, PaymentMethodEnum
)
from backend.api.routes.payments import _on_payment_success
from backend.api.routes.admin import get_admin_dashboard, get_admin_groups
from backend.api.routes.teacher import get_teacher_workspace

async def run_student_lifecycle_test():
    print("=" * 65)
    print("🚀 FULL STUDENT JOURNEY TEST: REGISTER -> PAY -> ENROLL -> TEACHER SYNC")
    print("=" * 65)

    test_student_id = 888123456
    test_name = "Dilshod Karimov"
    test_phone = "+998901239988"
    test_username = "dilshod_test"

    async with async_session() as session:
        # Clean up previous test run if exists
        from sqlalchemy import delete
        await session.execute(delete(Payment).where(Payment.student_id == test_student_id))
        await session.execute(delete(Enrollment).where(Enrollment.student_id == test_student_id))
        await session.execute(delete(User).where(User.id == test_student_id))
        await session.commit()

    # ----------------------------------------------------
    # STEP 1: STUDENT REGISTRATION
    # ----------------------------------------------------
    print("\n[STEP 1] Registering new Telegram student...")
    async with async_session() as session:
        new_student = User(
            id=test_student_id,
            full_name=test_name,
            phone=test_phone,
            username=test_username,
            language=LanguageEnum.uz,
            role=RoleEnum.student,
            is_active=True,
            created_at=datetime.utcnow()
        )
        session.add(new_student)
        await session.commit()
    print(f"✅ Student registered: ID={test_student_id}, Name={test_name}, Role=student")

    # ----------------------------------------------------
    # STEP 2: COURSE & GROUP SELECTION
    # ----------------------------------------------------
    print("\n[STEP 2] Browsing active courses and selecting group...")
    async with async_session() as session:
        from sqlalchemy import select
        target_group = (await session.execute(
            select(Group).where(Group.is_active == True).limit(1)
        )).scalar_one()
        course = await session.get(Course, target_group.course_id)
        
        # Initial enrolled count before payment
        from sqlalchemy import func
        init_count = (await session.execute(
            select(func.count(Enrollment.id))
            .where(Enrollment.group_id == target_group.id, Enrollment.is_active == True)
        )).scalar() or 0
        print(f"Selected Group: '{target_group.name}' | Course: '{course.title.get('uz') if isinstance(course.title, dict) else course.title}'")
        print(f"Price: {course.price:,.0f} UZS | Initial active students: {init_count} / {target_group.max_students}")

    # ----------------------------------------------------
    # STEP 3: CREATING & EXECUTING PAYMENT (Online Click / Payme)
    # ----------------------------------------------------
    print("\n[STEP 3] Student pays for the course...")
    async with async_session() as session:
        new_payment = Payment(
            student_id=test_student_id,
            group_id=target_group.id,
            amount=course.price,
            method=PaymentMethodEnum.click,
            status=PaymentStatusEnum.pending,
            created_at=datetime.utcnow()
        )
        session.add(new_payment)
        await session.commit()
        payment_id = new_payment.id
    print(f"Pending payment created: ID={payment_id}, Amount={course.price:,.0f} UZS")

    # Simulate payment provider webhook confirmation (Click Complete)
    print("Simulating Click webhook success confirmation...")
    await _on_payment_success(payment_id=payment_id, transaction_id="TEST_TX_998877", provider_name="click")

    # Verify payment confirmed and enrollment created
    async with async_session() as session:
        pay = await session.get(Payment, payment_id)
        assert pay.status == PaymentStatusEnum.confirmed, "Payment must be confirmed!"
        
        enr = (await session.execute(
            select(Enrollment).where(Enrollment.student_id == test_student_id, Enrollment.group_id == target_group.id)
        )).scalar_one_or_none()
        assert enr is not None, "Enrollment must be created after payment confirmation!"
        assert enr.status == EnrollmentStatusEnum.active, "Enrollment status must be active!"
        assert enr.is_active is True, "Enrollment must be active in group!"
    print("✅ Payment confirmed & student enrolled in group successfully!")

    # ----------------------------------------------------
    # STEP 4: VERIFY ADMIN DASHBOARD UPDATES
    # ----------------------------------------------------
    print("\n[STEP 4] Checking Admin Dashboard & Group Capacity...")
    mock_admin = {"id": 1435473812}
    admin_groups = await get_admin_groups(user=mock_admin)
    updated_group = next(g for g in admin_groups if g["id"] == target_group.id)
    print(f"Group '{updated_group['name']}' new capacity: {updated_group['enrolled_students']} / {updated_group['max_students']}")
    assert updated_group["enrolled_students"] == init_count + 1, "Enrolled students count must increase by 1!"
    print("✅ Admin Dashboard capacity count verified: Increased accurately!")

    # ----------------------------------------------------
    # STEP 5: VERIFY TEACHER WORKSPACE SYNC
    # ----------------------------------------------------
    print("\n[STEP 5] Checking Teacher Workspace sync...")
    mock_teacher = {"id": target_group.teacher_id or 1435473812}
    teacher_ws = await get_teacher_workspace(user=mock_teacher)
    
    # Find group in teacher workspace
    tg_in_ws = next((g for g in teacher_ws["groups"] if g["id"] == target_group.id), None)
    assert tg_in_ws is not None, "Group must appear in teacher workspace!"
    
    student_ids_in_group = [s["id"] for s in tg_in_ws["students"]]
    assert test_student_id in student_ids_in_group, "New student must appear in Teacher's class roster!"
    print(f"Teacher class roster contains new student: '{test_name}' ({test_phone})")
    print("✅ Teacher Workspace verified: Student immediately visible to instructor!")

    # ----------------------------------------------------
    # STEP 6: CLEANUP
    # ----------------------------------------------------
    print("\n[STEP 6] Cleaning up test student data...")
    async with async_session() as session:
        await session.execute(delete(Payment).where(Payment.student_id == test_student_id))
        await session.execute(delete(Enrollment).where(Enrollment.student_id == test_student_id))
        await session.execute(delete(User).where(User.id == test_student_id))
        await session.commit()
    print("✅ Test data cleanly reset.")

    print("\n" + "=" * 65)
    print("🎉 FULL STUDENT LIFECYCLE TEST PASSED 100%!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_student_lifecycle_test())
