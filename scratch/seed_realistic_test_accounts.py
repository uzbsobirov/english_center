import sys
import asyncio
from datetime import datetime, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.database import async_session
from backend.models import (
    User, RoleEnum, LanguageEnum, Course, Group,
    Enrollment, EnrollmentStatusEnum, Payment, PaymentStatusEnum, PaymentMethodEnum,
    Attendance, AttendanceStatusEnum, LevelEnum, TestResult, Test
)

async def seed_realistic_accounts():
    print("=" * 60)
    print("🌱 SEEDING REALISTIC TEST ACCOUNTS, COURSES & ROSTERS")
    print("=" * 60)

    async with async_session() as session:
        from sqlalchemy import select, delete

        # 1. Existing group and course
        group1 = (await session.execute(select(Group).where(Group.name == "GA | Odd"))).scalar_one_or_none()
        if not group1:
            group1 = (await session.execute(select(Group).limit(1))).scalar_one()

        course1 = await session.get(Course, group1.course_id)

        # 2. Add Second Course: IELTS Intensive (Band 7.0+)
        ielts_course = (await session.execute(select(Course).where(Course.level == LevelEnum.B2))).scalars().first()
        if not ielts_course:
            ielts_course = Course(
                title={"uz": "IELTS Intensive (Band 7.0+)", "ru": "IELTS Интенсив", "en": "IELTS Intensive"},
                description={"uz": "IELTS imtihoniga professional 3 oylik tayyorgarlik kursi", "ru": "Интенсивная подготовка к IELTS", "en": "Comprehensive IELTS preparation"},
                price=450000.0,
                price_per_lesson=37500.0,
                level=LevelEnum.B2,
                duration_months=3,
                lessons_per_week=3,
                is_active=True
            )
            session.add(ielts_course)
            await session.flush()
            print(f"✅ Created Course: IELTS Intensive (ID: {ielts_course.id}, Price: 450,000 UZS)")

        # 3. Add Second Group assigned to Teacher Zem (7195359577)
        group2 = (await session.execute(select(Group).where(Group.name == "IELTS-1 | Even"))).scalar_one_or_none()
        if not group2:
            group2 = Group(
                course_id=ielts_course.id,
                name="IELTS-1 | Even",
                teacher_id=7195359577, # Teacher Zem
                schedule=[{"day": "Tuesday", "time": "16:00"}, {"day": "Thursday", "time": "16:00"}, {"day": "Saturday", "time": "16:00"}],
                room="2-xona (IELTS Lab)",
                max_students=12,
                group_chat_link="https://t.me/+IELTS_Intensive_Alpha",
                is_active=True
            )
            session.add(group2)
            await session.flush()
            print(f"✅ Created Group: IELTS-1 | Even (Teacher: Zem 7195359577, Room: 2-xona)")

        # 4. Realistic Students for Group 1 (GA | Odd - Teacher: Anvar Sobirov)
        students_g1 = [
            {"id": 700100101, "name": "Madina Usmonova", "phone": "+998901112233", "user": "madina_u", "method": PaymentMethodEnum.click},
            {"id": 700100102, "name": "Jasur Bekmirzayev", "phone": "+998912223344", "user": "jasur_bek", "method": PaymentMethodEnum.payme},
            {"id": 700100103, "name": "Sevara Alimova", "phone": "+998933334455", "user": "sevara_al", "method": PaymentMethodEnum.cash},
            {"id": 700100104, "name": "Bobur Shokirov", "phone": "+998944445566", "user": "bobur_sh", "method": PaymentMethodEnum.click},
            {"id": 700100105, "name": "Dildora Rahimova", "phone": "+998975556677", "user": "dildora_r", "method": PaymentMethodEnum.payme},
        ]

        for s_data in students_g1:
            u = await session.get(User, s_data["id"])
            if not u:
                u = User(
                    id=s_data["id"],
                    full_name=s_data["name"],
                    phone=s_data["phone"],
                    username=s_data["user"],
                    role=RoleEnum.student,
                    language=LanguageEnum.uz,
                    is_active=True,
                    created_at=datetime.utcnow() - timedelta(days=15)
                )
                session.add(u)
                await session.flush()

            # Add confirmed payment
            p = (await session.execute(select(Payment).where(Payment.student_id == u.id, Payment.group_id == group1.id))).scalars().first()
            if not p:
                p = Payment(
                    student_id=u.id,
                    group_id=group1.id,
                    amount=course1.price,
                    method=s_data["method"],
                    status=PaymentStatusEnum.confirmed,
                    paid_at=datetime.utcnow() - timedelta(days=14),
                    created_at=datetime.utcnow() - timedelta(days=14)
                )
                session.add(p)

            # Add active enrollment
            enr = (await session.execute(select(Enrollment).where(Enrollment.student_id == u.id, Enrollment.group_id == group1.id))).scalars().first()
            if not enr:
                enr = Enrollment(
                    student_id=u.id,
                    group_id=group1.id,
                    status=EnrollmentStatusEnum.active,
                    is_active=True,
                    enrolled_at=datetime.utcnow() - timedelta(days=14)
                )
                session.add(enr)

            # Add attendance
            att = (await session.execute(select(Attendance).where(Attendance.student_id == u.id, Attendance.group_id == group1.id))).scalars().first()
            if not att:
                session.add(Attendance(
                    student_id=u.id,
                    group_id=group1.id,
                    lesson_date=datetime.now().date(),
                    status=AttendanceStatusEnum.present,
                    marked_by=1435473812
                ))

        print(f"✅ Enrolled {len(students_g1)} active students into Group 1 ('{group1.name}')")

        # 5. Realistic Students for Group 2 (IELTS-1 - Teacher: Zem)
        students_g2 = [
            {"id": 700200201, "name": "Azizbek Tursunov", "phone": "+998909998811", "user": "azizbek_t", "method": PaymentMethodEnum.click},
            {"id": 700200202, "name": "Kamola Karimova", "phone": "+998937776622", "user": "kamola_k", "method": PaymentMethodEnum.payme},
            {"id": 700200203, "name": "Sardor Yoqubov", "phone": "+998971113344", "user": "sardor_y", "method": PaymentMethodEnum.cash},
        ]

        for s_data in students_g2:
            u = await session.get(User, s_data["id"])
            if not u:
                u = User(
                    id=s_data["id"],
                    full_name=s_data["name"],
                    phone=s_data["phone"],
                    username=s_data["user"],
                    role=RoleEnum.student,
                    language=LanguageEnum.uz,
                    is_active=True,
                    created_at=datetime.utcnow() - timedelta(days=10)
                )
                session.add(u)
                await session.flush()

            p = (await session.execute(select(Payment).where(Payment.student_id == u.id, Payment.group_id == group2.id))).scalars().first()
            if not p:
                p = Payment(
                    student_id=u.id,
                    group_id=group2.id,
                    amount=ielts_course.price,
                    method=s_data["method"],
                    status=PaymentStatusEnum.confirmed,
                    paid_at=datetime.utcnow() - timedelta(days=9),
                    created_at=datetime.utcnow() - timedelta(days=9)
                )
                session.add(p)

            enr = (await session.execute(select(Enrollment).where(Enrollment.student_id == u.id, Enrollment.group_id == group2.id))).scalars().first()
            if not enr:
                enr = Enrollment(
                    student_id=u.id,
                    group_id=group2.id,
                    status=EnrollmentStatusEnum.active,
                    is_active=True,
                    enrolled_at=datetime.utcnow() - timedelta(days=9)
                )
                session.add(enr)

            att = (await session.execute(select(Attendance).where(Attendance.student_id == u.id, Attendance.group_id == group2.id))).scalars().first()
            if not att:
                session.add(Attendance(
                    student_id=u.id,
                    group_id=group2.id,
                    lesson_date=datetime.now().date(),
                    status=AttendanceStatusEnum.present,
                    marked_by=7195359577
                ))

        print(f"✅ Enrolled {len(students_g2)} active students into Group 2 ('{group2.name}')")

        # 6. One Pending Payment Student (e.g. for testing approval in cashier/payments)
        pending_u = await session.get(User, 700300301)
        if not pending_u:
            pending_u = User(
                id=700300301,
                full_name="Otabek Norov",
                phone="+998998887766",
                username="otabek_n",
                role=RoleEnum.student,
                language=LanguageEnum.uz,
                is_active=True,
                created_at=datetime.utcnow() - timedelta(hours=2)
            )
            session.add(pending_u)
            await session.flush()

        pending_p = (await session.execute(select(Payment).where(Payment.student_id == pending_u.id))).scalars().first()
        if not pending_p:
            pending_p = Payment(
                student_id=pending_u.id,
                group_id=group1.id,
                amount=course1.price,
                method=PaymentMethodEnum.cash,
                status=PaymentStatusEnum.pending,
                created_at=datetime.utcnow() - timedelta(hours=2)
            )
            session.add(pending_p)
        print("✅ Added Pending Payment Student: 'Otabek Norov' (Waiting for cash confirmation)")

        await session.commit()

    print("\n" + "=" * 60)
    print("🎉 REALISTIC ACCOUNTS SUCCESSFULLY SEEDED!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(seed_realistic_accounts())
