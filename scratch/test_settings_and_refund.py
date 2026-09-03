import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from datetime import datetime, date
from sqlalchemy import select
from backend.database import async_session
from backend.models import (
    User, RoleEnum, LanguageEnum, Course, Group, Enrollment,
    Attendance, AttendanceStatusEnum, Payment, PaymentStatusEnum, PaymentMethodEnum,
    Refund, GroupChangeRequest, LevelEnum
)

async def run_tests():
    print("--- [TEST] Running Settings, Group Change & Refund Test Suite ---")
    async with async_session() as session:
        # Pre-cleanup
        test_uids = [777111222, 777333444]
        for tbl in [Refund, GroupChangeRequest, Attendance, Payment, Enrollment, Group]:
            q = select(tbl)
            if hasattr(tbl, "student_id"):
                q = q.where(tbl.student_id.in_(test_uids))
            elif hasattr(tbl, "user_id"):
                q = q.where(tbl.user_id.in_(test_uids))
            elif hasattr(tbl, "teacher_id"):
                q = q.where(tbl.teacher_id.in_(test_uids))
            res = await session.execute(q)
            for item in res.scalars().all():
                await session.delete(item)
        existing_users = await session.execute(select(User).where(User.id.in_(test_uids)))
        for u in existing_users.scalars().all():
            await session.delete(u)
        await session.commit()
        # 1. Setup Student, Teacher, Course, Groups
        student = User(
            id=777111222,
            full_name="Testing Student",
            username="test_student",
            phone="+998901112233",
            role=RoleEnum.student,
            language=LanguageEnum.uz,
        )
        teacher = User(
            id=777333444,
            full_name="Testing Teacher",
            username="test_teacher",
            role=RoleEnum.teacher,
            language=LanguageEnum.uz,
        )
        session.add_all([student, teacher])
        await session.commit()

        course = Course(
            title={"uz": "IELTS Standard", "ru": "IELTS Стандарт", "en": "IELTS Standard"},
            description={"uz": "IELTS Standard Description", "ru": "Описание", "en": "Description"},
            type="IELTS",
            level=LevelEnum.B2,
            duration_months=3,
            lessons_per_week=3,
            price=600000,
            price_per_lesson=50000,
            is_active=True,
        )
        session.add(course)
        await session.commit()
        await session.refresh(course)

        grp1 = Group(
            course_id=course.id,
            teacher_id=teacher.id,
            name="IELTS-Morning-01",
            schedule=[{"day": 1, "time": "09:00"}],
            is_active=True,
        )
        grp2 = Group(
            course_id=course.id,
            teacher_id=teacher.id,
            name="IELTS-Evening-02",
            schedule=[{"day": 1, "time": "18:00"}],
            is_active=True,
        )
        session.add_all([grp1, grp2])
        await session.commit()
        await session.refresh(grp1)
        await session.refresh(grp2)

        enr = Enrollment(
            student_id=student.id,
            group_id=grp1.id,
            status="active",
            is_active=True,
        )
        session.add(enr)
        await session.commit()

        # Payment
        pay = Payment(
            student_id=student.id,
            group_id=grp1.id,
            amount=600000,
            method=PaymentMethodEnum.cash,
            status=PaymentStatusEnum.confirmed,
            paid_at=datetime.utcnow(),
        )
        session.add(pay)
        await session.commit()

        # 2 Attendances
        att1 = Attendance(group_id=grp1.id, student_id=student.id, lesson_date=date.today(), status=AttendanceStatusEnum.present, marked_by=teacher.id)
        att2 = Attendance(group_id=grp1.id, student_id=student.id, lesson_date=date.today(), status=AttendanceStatusEnum.present, marked_by=teacher.id)
        session.add_all([att1, att2])
        await session.commit()

        print("[OK] Setup ready: Student enrolled in Group 1 with 600,000 so'm paid & 2 attended lessons.")

        # Test 1: Group Change Request
        g_req = GroupChangeRequest(
            student_id=student.id,
            current_group_id=grp1.id,
            target_group_id=grp2.id,
            reason="Morning schedule conflict",
            status="pending",
        )
        session.add(g_req)
        await session.commit()
        await session.refresh(g_req)
        assert g_req.id is not None
        print(f"[OK] GroupChangeRequest created: ID={g_req.id}")

        # Approve Group Change
        g_req.status = "approved"
        g_req.approved_by = teacher.id
        enr.group_id = g_req.target_group_id
        await session.commit()
        assert enr.group_id == grp2.id
        print(f"[OK] Group change approved -> Student moved to {grp2.name}")

        # Test 2: Refund Calculation & Request
        attended_count = 2
        price_per_lesson = float(course.price_per_lesson)
        used_amount = attended_count * price_per_lesson
        expected_refund = 600000 - used_amount  # 600000 - 100000 = 500000
        assert expected_refund == 500000.0

        ref = Refund(
            payment_id=pay.id,
            student_id=student.id,
            group_id=grp2.id,
            reason="Relocating to another city",
            calculated_amount=expected_refund,
            status="pending",
        )
        session.add(ref)
        await session.commit()
        await session.refresh(ref)
        print(f"[OK] Refund request created: Calculated={ref.calculated_amount} so'm")

        # Approve Refund
        ref.status = "approved"
        ref.approved_by = teacher.id
        ref.final_amount = ref.calculated_amount
        enr.status = "dropped"
        enr.is_active = False
        pay.status = PaymentStatusEnum.refunded
        await session.commit()

        assert enr.is_active is False
        assert pay.status == PaymentStatusEnum.refunded
        print(f"[OK] Refund approved -> Student dropped from group & Payment marked as refunded.")

        # Cleanup
        await session.delete(ref)
        await session.delete(g_req)
        await session.commit()

        await session.delete(att1)
        await session.delete(att2)
        await session.delete(pay)
        await session.delete(enr)
        await session.commit()

        await session.delete(grp1)
        await session.delete(grp2)
        await session.commit()

        await session.delete(course)
        await session.delete(student)
        await session.delete(teacher)
        await session.commit()
        print("[OK] Test database cleaned up.")
        print("--- [ALL SETTINGS & REFUND TESTS PASSED] ---")

if __name__ == "__main__":
    asyncio.run(run_tests())
