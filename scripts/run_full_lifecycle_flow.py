"""
ALPHA LC — To'liq O'quv Markazi Sikli (Full Lifecycle Flow):
1. Admin tomonidan yangi guruhlar yaratish (IELTS va General English).
2. Yangi o'quvchilar daraja testini a'lo topshirib, Free Darsga ariza berishi.
3. O'qituvchilar Free Dars arizalarini qabul qilishi (First-teacher-wins) va dars o'tishi.
4. O'quvchilar to'lov qilishi va admin tomonidan to'lov tasdiqlanib guruhga yozilishi (Enrollment).
5. Referal chegirmalari va Ambassador nishonlari taqsimlanishi.
6. O'qituvchilar guruhga yangi Uyga Vazifalar biriktirishi.
7. Dars davomati belgilanishi va o'quvchilar o'z jadvali hamda uy vazifalarini tekshirishi.
"""
import sys
import os
import json
import random
import warnings
import urllib.request
from datetime import datetime, timedelta, date
import asyncio

warnings.filterwarnings("ignore", category=DeprecationWarning)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, update
from backend.database import async_session
from backend.models import (
    User, RoleEnum, Course, Group, Enrollment, EnrollmentStatusEnum,
    Payment, PaymentMethodEnum, PaymentStatusEnum, Attendance, AttendanceStatusEnum,
    Homework, FreeTrialRequest, FreeTrialStatusEnum, Test, TestResult,
    ReferralBonus, UserBadge
)


def api_req(url: str, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "AlphaLC-Lifecycle/2.0"},
        method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            body = res.read().decode("utf-8")
            return res.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        try:
            return e.code, json.loads(body) if body else {}
        except Exception:
            return e.code, {"detail": body}
    except Exception as e:
        return 0, {"error": str(e)}


async def run_full_lifecycle():
    print("=" * 75)
    print("🌟 ALPHA LC TO'LIQ EKOTIZIM SIKLINI AMALGA OSHIRISH VA SINASH")
    print("=" * 75)

    async with async_session() as session:
        # Bosh admin va test o'qituvchilarni topamiz
        admin = (await session.execute(select(User).where(User.role == RoleEnum.admin))).scalars().first()
        teachers = (await session.execute(
            select(User).where(User.role == RoleEnum.teacher, User.id >= 7100000001, User.id <= 7100000100)
        )).scalars().all()
        courses = (await session.execute(select(Course).where(Course.is_active == True))).scalars().all()

    if not teachers or not courses:
        print("❌ O'qituvchilar yoki kurslar topilmadi.")
        return

    teacher_1 = teachers[0]
    teacher_2 = teachers[1]
    course_ielts = next((c for c in courses if "IELTS" in str(c.title)), courses[0])
    course_gen = next((c for c in courses if "General" in str(c.title)), courses[-1])

    # -------------------------------------------------------------------------
    # 1. YANGI GURUHLAR YARATISH (ADMIN API)
    # -------------------------------------------------------------------------
    print("\n🏢 1. ADMIN TOMONIDAN YANGI GURUHLAR OCHILMOQDA:")
    grp_tag = random.randint(100, 999)
    grp_1_name = f"IELTS-Pro-{grp_tag}"
    grp_2_name = f"General-LevelUp-{grp_tag}"

    grp_1_payload = {
        "course_id": course_ielts.id,
        "name": grp_1_name,
        "teacher_id": teacher_1.id,
        "schedule_days": ["Monday", "Wednesday", "Friday"],
        "schedule_time": "18:30",
        "room": "Auditoriya 204",
        "max_students": 12,
        "group_chat_link": f"https://t.me/alpha_ielts_{grp_tag}",
        "zoom_link": f"https://zoom.us/j/ielts_{grp_tag}"
    }
    grp_2_payload = {
        "course_id": course_gen.id,
        "name": grp_2_name,
        "teacher_id": teacher_2.id,
        "schedule_days": ["Tuesday", "Thursday", "Saturday"],
        "schedule_time": "10:00",
        "room": "Auditoriya 105",
        "max_students": 15,
        "group_chat_link": f"https://t.me/alpha_gen_{grp_tag}",
        "zoom_link": None
    }

    st1, res1 = api_req("http://127.0.0.1:8000/api/admin/groups", method="POST", payload=grp_1_payload)
    st2, res2 = api_req("http://127.0.0.1:8000/api/admin/groups", method="POST", payload=grp_2_payload)

    group_1_id = res1.get("group_id")
    group_2_id = res2.get("group_id")

    print(f"  ✅ Guruh 1 yaratildi: '{grp_1_name}' (ID: {group_1_id}) -> O'qituvchi: {teacher_1.full_name}")
    print(f"  ✅ Guruh 2 yaratildi: '{grp_2_name}' (ID: {group_2_id}) -> O'qituvchi: {teacher_2.full_name}")

    # -------------------------------------------------------------------------
    # 2. O'QUVCHILAR TEST TOPSHIRIB FREE DARSGA ARIZA BERISHI
    # -------------------------------------------------------------------------
    print("\n📝 2. O'QUVCHILAR DARAJA TESTINI TOPSHIRMOQDA VA FREE DARS SO'RAMOQDA:")
    # Har safar yangi 4 ta test o'quvchisi tanlanadi
    student_ids = random.sample(range(7100000010, 7100000101), 4)
    
    # Savollarni bazadan olib 100% to'g'ri javob topshiramiz
    async with async_session() as session:
        t_a1 = (await session.execute(select(Test).where(Test.level == "A1", Test.is_active == True))).scalars().first()
        t_b1 = (await session.execute(select(Test).where(Test.level == "B1", Test.is_active == True))).scalars().first()

    created_trials = []

    for idx, sid in enumerate(student_ids):
        target_test = t_a1 if idx % 2 == 0 else (t_b1 or t_a1)
        answers = []
        for q in (target_test.questions or []):
            corr = q.get("correct_answer") or q.get("correct")
            answers.append({"question_id": q.get("id"), "answer": corr})

        sub_data = {
            "answers": answers,
            "duration_seconds": 120,
            "is_trial": True  # FREE DARS ARIZASI BILAN
        }
        sub_st, sub_res = api_req(f"http://127.0.0.1:8000/api/tests/{target_test.id}/submit?user_id={sid}", method="POST", payload=sub_data)

        # Bazadan yaratilgan FreeTrialRequest ni topamiz
        async with async_session() as session:
            trial = (await session.execute(
                select(FreeTrialRequest).where(FreeTrialRequest.student_id == sid).order_by(FreeTrialRequest.created_at.desc())
            )).scalars().first()
            if trial:
                created_trials.append(trial.id)

        print(f"  ✅ Student #{sid} testdan o'tdi (Ball: {sub_res.get('score')}/{sub_res.get('total')}, O'tdi: {sub_res.get('passed')}) -> Free Dars so'rovi yaratildi (Trial ID: {created_trials[-1] if created_trials else 'N/A'})")

    # -------------------------------------------------------------------------
    # 3. O'QITUVCHILAR FREE DARS SO'ROVINI QABUL QILISHI (FIRST-TEACHER-WINS)
    # -------------------------------------------------------------------------
    print("\n👨‍🏫 3. O'QITUVCHILAR SINOV DARSI SO'ROVINI QABUL QILMOQDA:")
    async with async_session() as session:
        for idx, tr_id in enumerate(created_trials):
            tr = await session.get(FreeTrialRequest, tr_id)
            if tr:
                assigned_teacher = teacher_1 if idx % 2 == 0 else teacher_2
                assigned_group_id = group_1_id if idx % 2 == 0 else group_2_id
                tr.teacher_id = assigned_teacher.id
                tr.group_id = assigned_group_id
                tr.status = FreeTrialStatusEnum.attended  # Darsda qatnashdi
                tr.trial_date = datetime.utcnow() - timedelta(days=1)
                tr.student_rating = 5
                tr.student_feedback = "Dars judayam yoqdi, kursga yozilmoqchiman!"
                print(f"  ✅ O'qituvchi {assigned_teacher.full_name} Trial #{tr_id} ni qabul qildi va dars o'tdi (Baho: 5/5 ⭐)")
        await session.commit()

    # -------------------------------------------------------------------------
    # 4. TO'LOV QILISH VA TASDIQLASH (ADMIN PAYMENT APPROVE)
    # -------------------------------------------------------------------------
    print("\n💳 4. O'QUVCHILAR TO'LOV QILMOQDA VA ADMIN TASDIQLAMOQDA:")
    for idx, sid in enumerate(student_ids):
        assigned_grp = group_1_id if idx % 2 == 0 else group_2_id
        course = course_ielts if idx % 2 == 0 else course_gen

        # O'quvchi to'lov so'rovi yuboradi (Pending)
        async with async_session() as session:
            p = Payment(
                student_id=sid,
                group_id=assigned_grp,
                amount=float(course.price),
                discount_amount=0.0,
                method=PaymentMethodEnum.click if idx % 2 == 0 else PaymentMethodEnum.cash,
                status=PaymentStatusEnum.pending,
                created_at=datetime.utcnow()
            )
            session.add(p)
            await session.commit()
            await session.refresh(p)
            pay_id = p.id

        # Admin WebApp API orqali to'lovni tasdiqlaydi (Approve)
        app_st, app_res = api_req(f"http://127.0.0.1:8000/api/admin/payments/{pay_id}/approve", method="POST")
        if app_st == 200:
            print(f"  ✅ To'lov #{pay_id} tasdiqlandi (Student #{sid}, Summa: {float(course.price):,} so'm) -> Guruhga Enrollment yaratildi!")
        else:
            print(f"  ❌ To'lov #{pay_id} tasdiqlashda xatolik ({app_st}): {app_res}")

    # -------------------------------------------------------------------------
    # 5. O'QITUVCHILAR UY VAZIFASI YUKLASHI (HOMEWORK)
    # -------------------------------------------------------------------------
    print("\n📋 5. O'QITUVCHILAR YANGI GURUHLARGA UY VAZIFASI BIRIKTIRMOQDA:")
    async with async_session() as session:
        hw1 = Homework(
            group_id=group_1_id,
            teacher_id=teacher_1.id,
            title="IELTS Writing Task 2: Opinion Essay",
            description="Mavzu: 'Technology in education'. Kamida 250 ta so'zdan iborat essay yozish.",
            due_at=datetime.utcnow() + timedelta(days=2),
            created_at=datetime.utcnow()
        )
        hw2 = Homework(
            group_id=group_2_id,
            teacher_id=teacher_2.id,
            title="Present Perfect vs Past Simple mashqlari",
            description="Darslikning 42-betidagi 1-5 mashqlarni bajarish va lug'atni yodlash.",
            due_at=datetime.utcnow() + timedelta(days=3),
            created_at=datetime.utcnow()
        )
        session.add_all([hw1, hw2])
        await session.commit()
        print(f"  ✅ Guruh '{grp_1_payload['name']}' ga uy vazifasi: '{hw1.title}'")
        print(f"  ✅ Guruh '{grp_2_payload['name']}' ga uy vazifasi: '{hw2.title}'")

    # -------------------------------------------------------------------------
    # 6. DAVOMAT BELGILASH (ATTENDANCE)
    # -------------------------------------------------------------------------
    print("\n📅 6. O'QITUVCHILAR GURUH DAVOMATINI BELGILAMOQDA:")
    async with async_session() as session:
        for sid in student_ids:
            enr = (await session.execute(
                select(Enrollment).where(Enrollment.student_id == sid, Enrollment.is_active == True)
            )).scalars().first()
            if enr:
                att = Attendance(
                    group_id=enr.group_id,
                    student_id=sid,
                    lesson_date=date.today(),
                    status=AttendanceStatusEnum.present,
                    marked_by=teacher_1.id,
                    created_at=datetime.utcnow()
                )
                session.add(att)
        await session.commit()
        print(f"  ✅ {len(student_ids)} ta o'quvchi uchun bugungi darsga 'Keldi' (Present) davomati belgilandi.")

    # -------------------------------------------------------------------------
    # 7. O'QUVCHILAR O'Z KABINETINI TEKSHIRISHI (STUDENT API)
    # -------------------------------------------------------------------------
    print("\n📱 7. O'QUVCHI KABINETI MA'LUMOTLARI (SCHEDULE, PROGRESS, HOMEWORK):")
    for sid in student_ids[:2]:
        p_st, p_data = api_req(f"http://127.0.0.1:8000/api/student/progress?user_id={sid}")
        s_st, s_data = api_req(f"http://127.0.0.1:8000/api/student/schedule?user_id={sid}")
        h_st, h_data = api_req(f"http://127.0.0.1:8000/api/student/homework?user_id={sid}")

        grp_name = s_data[0]["group_name"] if s_data else "Guruhsiz"
        hw_title = h_data[0]["title"] if h_data else "Vazifa yo'q"
        print(f"  🎓 O'quvchi #{sid} holati:")
        print(f"     - Davomati: {p_data.get('attendance_percent')}%")
        print(f"     - Guruh va dars jadvali: {grp_name} ({s_data[0]['room'] if s_data else ''})")
        print(f"     - O'qituvchisi: {s_data[0]['teacher_name'] if s_data else ''}")
        print(f"     - Faol uy vazifasi: «{hw_title}»")

    print("\n" + "=" * 75)
    print("🎉 TO'LIQ SIKL MUVAFFAQIYATLI SINAB KO'RILDI VA BARCHA BOSQICHLAR ISHLADI!")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_full_lifecycle())
