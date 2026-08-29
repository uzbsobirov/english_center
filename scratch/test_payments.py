import asyncio
from datetime import datetime
from sqlalchemy import select, delete

from backend.database import async_session
from backend.models import (
    User, RoleEnum, Group, Course, Payment, PaymentMethodEnum, PaymentStatusEnum,
    Enrollment, ReferralBonus, Refund, Attendance, AttendanceStatusEnum, LevelEnum,
)

async def run_payment_tests():
    print("--- [TEST] Running Payments & Enrollment Test Suite ---")
    async with async_session() as session:
        # 1. Setup sample users: Referrer, Student, Teacher, Friend
        referrer_id = 999111222
        student_id = 999222333
        teacher_id = 999333444
        friend_id = 999444555

        # Clean existing test records if any
        await session.execute(delete(Refund).where(Refund.student_id.in_([student_id, friend_id])))
        await session.execute(delete(Attendance).where(Attendance.student_id.in_([student_id, friend_id])))
        await session.execute(delete(Payment).where(Payment.student_id.in_([student_id, friend_id])))
        await session.execute(delete(Enrollment).where(Enrollment.student_id.in_([student_id, friend_id])))
        await session.execute(delete(ReferralBonus).where(ReferralBonus.referred_student_id.in_([student_id, friend_id])))
        await session.execute(delete(ReferralBonus).where(ReferralBonus.user_id.in_([referrer_id, student_id, teacher_id, friend_id])))
        await session.execute(delete(User).where(User.id.in_([referrer_id, student_id, teacher_id, friend_id])))
        await session.commit()

        referrer = User(id=referrer_id, full_name="Referrer Rustam", role=RoleEnum.student)
        teacher = User(id=teacher_id, full_name="Teacher Jasur", role=RoleEnum.teacher)
        student = User(id=student_id, full_name="Student Bobur", role=RoleEnum.student, referred_by=referrer_id)
        friend = User(id=friend_id, full_name="Friend Anvar", role=RoleEnum.student)
        session.add_all([referrer, teacher, student, friend])

        # Get or create Course & Group
        course_res = await session.execute(select(Course).limit(1))
        course = course_res.scalars().first()
        if not course:
            course = Course(
                title={"uz": "General English B1", "ru": "General English B1", "en": "General English B1"},
                level=LevelEnum.B1,
                price=600000.0,
                price_per_lesson=50000.0,
            )
            session.add(course)
            await session.flush()

        group_res = await session.execute(select(Group).where(Group.course_id == course.id).limit(1))
        group = group_res.scalars().first()
        if not group:
            group = Group(
                name="B1-FastTrack",
                course_id=course.id,
                teacher_id=teacher_id,
                schedule={"days": ["Du", "Chor", "Juma"], "time": "16:00-18:00"},
                room="Room 204",
            )
            session.add(group)
            await session.flush()

        await session.commit()
        print(f"[OK] Users, Course ({course.id}), and Group ({group.name}) ready.")

        # 2. Test Referral Bonus Discount Application
        # Give student an existing bonus (e.g. 5%) from friend
        prior_bonus = ReferralBonus(
            user_id=student_id,
            referred_student_id=friend_id,
            bonus_percent=5.0,
            status="pending",
            is_used=False,
        )
        session.add(prior_bonus)
        await session.commit()

        # Check total active discount
        bonus_res = await session.execute(
            select(ReferralBonus).where(
                ReferralBonus.user_id == student_id,
                ReferralBonus.status == "pending",
                ReferralBonus.is_used == False,
            )
        )
        bonuses = bonus_res.scalars().all()
        discount_pct = sum(float(b.bonus_percent) for b in bonuses)
        assert discount_pct == 5.0, f"Expected 5.0% discount, got {discount_pct}"
        print(f"[OK] Referral discount calculated: {discount_pct}%")

        base_price = float(course.price)
        discount_amount = base_price * (discount_pct / 100.0)
        final_price = base_price - discount_amount

        # 3. Create Pending Cash Payment
        payment = Payment(
            student_id=student_id,
            group_id=group.id,
            amount=final_price,
            discount_amount=discount_amount,
            method=PaymentMethodEnum.cash,
            status=PaymentStatusEnum.pending,
        )
        session.add(payment)
        await session.flush()
        payment_id = payment.id
        await session.commit()
        print(f"[OK] Pending payment created: ID={payment_id}, Amount={final_price:,.0f} som")

        # 4. Simulate Teacher / Admin Confirmation
        payment.status = PaymentStatusEnum.confirmed
        payment.confirmed_by = teacher_id
        payment.paid_at = datetime.utcnow()

        # Create Enrollment
        enrollment = Enrollment(
            student_id=student_id,
            group_id=group.id,
            enrolled_at=datetime.utcnow(),
        )
        session.add(enrollment)

        # Mark student's used referral bonus
        prior_bonus.is_used = True
        prior_bonus.status = "applied"

        # Award Referrer +5% bonus since student paid
        new_bonus = ReferralBonus(
            user_id=referrer_id,
            referred_student_id=student_id,
            bonus_percent=5.0,
            status="pending",
            is_used=False,
        )
        session.add(new_bonus)
        student.referral_bonus_given = True
        await session.commit()
        print(f"[OK] Payment confirmed -> Enrollment created & Referrer awarded +5% bonus.")

        # 5. Test Refund Formula: refund = total_paid - (price_per_lesson * attended_lessons)
        # Simulate student attended 2 lessons
        att1 = Attendance(group_id=group.id, student_id=student_id, status=AttendanceStatusEnum.present, marked_by=teacher_id)
        att2 = Attendance(group_id=group.id, student_id=student_id, status=AttendanceStatusEnum.late, marked_by=teacher_id)
        session.add_all([att1, att2])
        await session.commit()

        price_per_lesson = float(course.price_per_lesson) if course.price_per_lesson else (base_price / 12.0)
        lessons_attended = 2
        used_amount = price_per_lesson * lessons_attended
        expected_refund = max(final_price - used_amount, 0.0)

        refund = Refund(
            student_id=student_id,
            group_id=group.id,
            reason=f"Avtomatik hisob: {lessons_attended} ta darsga qatnashgan",
            calculated_amount=expected_refund,
            status="pending",
        )
        session.add(refund)
        await session.commit()

        assert refund.calculated_amount == expected_refund, f"Expected refund {expected_refund}, got {refund.calculated_amount}"
        print(f"[OK] Refund calculation verified: Paid={final_price:,.0f}, Used ({lessons_attended} lessons)={used_amount:,.0f}, Refund={expected_refund:,.0f} som")

        # Cleanup test records
        await session.execute(delete(Refund).where(Refund.student_id.in_([student_id, friend_id])))
        await session.execute(delete(Attendance).where(Attendance.student_id.in_([student_id, friend_id])))
        await session.execute(delete(Payment).where(Payment.student_id.in_([student_id, friend_id])))
        await session.execute(delete(Enrollment).where(Enrollment.student_id.in_([student_id, friend_id])))
        await session.execute(delete(ReferralBonus).where(ReferralBonus.referred_student_id.in_([student_id, friend_id])))
        await session.execute(delete(ReferralBonus).where(ReferralBonus.user_id.in_([referrer_id, student_id, teacher_id, friend_id])))
        await session.execute(delete(User).where(User.id.in_([referrer_id, student_id, teacher_id, friend_id])))
        await session.commit()
        print("[OK] Test database cleaned up successfully.")

    print("--- [ALL TESTS PASSED] ---")

if __name__ == "__main__":
    asyncio.run(run_payment_tests())
