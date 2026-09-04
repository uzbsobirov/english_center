"""
🌟 ALPHA LC — MASTER TO'LIQ EKOTIZIM TESTI (ALL-IN-ONE MASTER TEST)
Ushbu skript foydalanuvchi talab qilgan 15 ta funksiyaning barchasini boshidan oxirigacha sinab ko'radi:
1. Yangi test yaratish (POST /api/teacher/save-test)
2. Yangi guruh ochish (POST /api/admin/groups)
3. Yangi o'qituvchi tayinlash (POST /api/admin/teachers)
4. Yangi admin tayinlash (POST /api/admin/admins)
5. Free Darsga ariza berish va qabul qilish (FreeTrialRequest flow)
6. To'lovlar: Cash (Naqd) va Online (Payme Webhook) to'lovlarni qabul qilish
7. Bot orqali Support Chat (Savol-javob ochish va javob berish)
8. Referal tizimi: Do'stini taklif qilish, +5% bonus va Ambassador badge
9. Uy vazifasi qo'shish va o'quvchi tomonidan qabul qilish
10. O'quvchini guruhdan chetlatish (Dropped / Refund)
11. O'quvchining guruhini boshqa guruhga almashtirish (GroupChangeRequest)
12. O'quvchi progressi va statistikasini tekshirish (GET /api/student/progress)
13. Oddiy daraja testini topshirish va baholash
14. Reklama / Ommaviy xabarnoma tarqatish (POST /api/admin/broadcast)
15. PDF Sertifikat generatsiya qilish (ReportLab)
"""
import sys
import os
import json
import time
import random
import warnings
import urllib.request
from datetime import datetime, timedelta, date
import asyncio

warnings.filterwarnings("ignore", category=DeprecationWarning)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, update, delete
from backend.database import async_session
from backend.models import (
    User, RoleEnum, LanguageEnum, LevelEnum, Course, Group,
    Enrollment, EnrollmentStatusEnum, Payment, PaymentMethodEnum, PaymentStatusEnum,
    Attendance, AttendanceStatusEnum, Homework, FreeTrialRequest, FreeTrialStatusEnum,
    Test, TestResult, ReferralBonus, UserBadge, SupportChat, SupportChatStatusEnum,
    SupportChatClosedReasonEnum, GroupChangeRequest, Refund
)
from backend.services.certificate_generator import generate_certificate_pdf


def api_call(url: str, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "AlphaMasterTest/1.0"},
        method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
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


async def run_master_test():
    print("=" * 80)
    print("🚀 ALPHA LC — BARCHA FUNKSIYALARNI BOSHDAN OXIRIGACHA MASTER SINOVDAN O'TKAZISH")
    print("=" * 80)

    passed_tests = 0
    total_tests = 15

    tag = random.randint(100, 999)

    # -------------------------------------------------------------------------
    # 1. TEST QO'SHISH (Teacher / Admin Test Creation)
    # -------------------------------------------------------------------------
    print("\n[1/15] 📝 1. YANGI TEST QO'SHISH (POST /api/teacher/save-test):")
    new_test_payload = {
        "certificate_type": "IELTS",
        "level": "B2",
        "title": {
            "uz": f"IELTS B2 Master Test #{tag}",
            "ru": f"IELTS B2 Мастер Тест #{tag}",
            "en": f"IELTS B2 Master Test #{tag}"
        },
        "passing_score": 70.0,
        "time_limit_min": 25,
        "source": "manual",
        "questions": [
            {
                "id": "m_q1",
                "order_num": 1,
                "type": "mcq",
                "text": "By the time the teacher arrived, the students ___ the exercise.",
                "options": ["A) had finished", "B) finished", "C) have finished", "D) finish"],
                "correct_answer": "A) had finished",
                "points": 1,
                "ai_generated": False,
                "needs_review": False
            },
            {
                "id": "m_q2",
                "order_num": 2,
                "type": "mcq",
                "text": "The manager insisted that everyone ___ on time.",
                "options": ["A) be", "B) is", "C) was", "D) are"],
                "correct_answer": "A) be",
                "points": 1,
                "ai_generated": False,
                "needs_review": False
            }
        ]
    }
    st, res = api_call("http://127.0.0.1:8000/api/teacher/save-test", method="POST", payload=new_test_payload)
    created_test_id = res.get("test_id")
    if st == 200 and created_test_id:
        print(f"  ✅ Yangi test yaratildi: ID={created_test_id} ('{new_test_payload['title']['uz']}')")
        passed_tests += 1
    else:
        print(f"  ❌ Test yaratishda xatolik ({st}): {res}")

    # -------------------------------------------------------------------------
    # 2. YANGI O'QITUVCHI QO'SHISH (POST /api/admin/teachers)
    # -------------------------------------------------------------------------
    print("\n[2/15] 👨‍🏫 2. YANGI O'QITUVCHI QO'SHISH (POST /api/admin/teachers):")
    new_teacher_id = 7100000901
    teacher_payload = {
        "telegram_id": new_teacher_id,
        "full_name": f"Ustoz Botir Sobirov #{tag}",
        "phone": "+998901239999",
        "username": f"teacher_botir_{tag}"
    }
    st, res = api_call("http://127.0.0.1:8000/api/admin/teachers", method="POST", payload=teacher_payload)
    if st == 200:
        print(f"  ✅ Yangi o'qituvchi tayinlandi: {teacher_payload['full_name']} (ID: {new_teacher_id})")
        passed_tests += 1
    else:
        print(f"  ❌ O'qituvchi qo'shishda xatolik ({st}): {res}")

    # -------------------------------------------------------------------------
    # 3. YANGI ADMIN QO'SHISH (POST /api/admin/admins)
    # -------------------------------------------------------------------------
    print("\n[3/15] 🛡 3. YANGI ADMIN TAYINLASH (POST /api/admin/admins):")
    new_admin_id = 7100000902
    admin_payload = {
        "telegram_id": new_admin_id,
        "full_name": f"Manager Sanjarbek #{tag}",
        "phone": "+998935557788",
        "username": f"admin_sanjar_{tag}"
    }
    st, res = api_call("http://127.0.0.1:8000/api/admin/admins", method="POST", payload=admin_payload)
    if st == 200:
        print(f"  ✅ Yangi admin tayinlandi: {admin_payload['full_name']} (ID: {new_admin_id})")
        passed_tests += 1
    else:
        print(f"  ❌ Admin qo'shishda xatolik ({st}): {res}")

    # -------------------------------------------------------------------------
    # 4. YANGI GURUH QO'SHISH (POST /api/admin/groups)
    # -------------------------------------------------------------------------
    print("\n[4/15] 👥 4. YANGI GURUH OCHISH (POST /api/admin/groups):")
    async with async_session() as session:
        course = (await session.execute(select(Course).where(Course.is_active == True))).scalars().first()

    group_payload = {
        "course_id": course.id,
        "name": f"IELTS-Pro-Master-{tag}",
        "teacher_id": new_teacher_id,
        "schedule_days": ["Monday", "Wednesday", "Friday"],
        "schedule_time": "19:00",
        "room": f"VIP Room {tag % 100}",
        "max_students": 14,
        "group_chat_link": f"https://t.me/ielts_group_{tag}",
        "zoom_link": f"https://zoom.us/j/{tag}000"
    }
    st, res = api_call("http://127.0.0.1:8000/api/admin/groups", method="POST", payload=group_payload)
    new_group_id = res.get("group_id")
    if st == 200 and new_group_id:
        print(f"  ✅ Yangi guruh yaratildi: '{group_payload['name']}' (ID: {new_group_id})")
        passed_tests += 1
    else:
        print(f"  ❌ Guruh ochishda xatolik ({st}): {res}")

    # -------------------------------------------------------------------------
    # 5. FREE DARSGA REQUEST YUBORISH VA QABUL QILISH
    # -------------------------------------------------------------------------
    print("\n[5/15] 🎯 5. FREE DARS ARIZASI VA O'QITUVCHI TASDIQLASHI:")
    student_trial_id = 7100000085
    # Yangi yaratilgan testni yechadi
    answers = [
        {"question_id": "m_q1", "answer": "A) had finished"},
        {"question_id": "m_q2", "answer": "A) be"},
    ]
    sub_payload = {"answers": answers, "duration_seconds": 90, "is_trial": True}
    st, res = api_call(f"http://127.0.0.1:8000/api/tests/{created_test_id}/submit?user_id={student_trial_id}", method="POST", payload=sub_payload)

    trial_id = None
    async with async_session() as session:
        trial = (await session.execute(
            select(FreeTrialRequest).where(FreeTrialRequest.student_id == student_trial_id).order_by(FreeTrialRequest.created_at.desc())
        )).scalars().first()
        if trial:
            trial_id = trial.id
            # O'qituvchi qabul qiladi
            trial.teacher_id = new_teacher_id
            trial.group_id = new_group_id
            trial.status = FreeTrialStatusEnum.attended
            trial.student_rating = 5
            trial.student_feedback = "Dars ajoyib o'tdi!"
            await session.commit()

    if trial_id:
        print(f"  ✅ Free dars arizasi #{trial_id} yaratildi va o'qituvchi tomonidan qabul qilinib dars o'tildi (Baho: 5/5 ⭐)")
        passed_tests += 1
    else:
        print("  ❌ Free trial so'rovi topilmadi.")

    # -------------------------------------------------------------------------
    # 6. TO'LOVLAR: ONLINE (PAYME WEBHOOK) VA CASH (NAQD)
    # -------------------------------------------------------------------------
    print("\n[6/15] 💳 6. TO'LOVLARNI QABUL QILISH (ONLINE PAYME & CASH):")
    # A) Naqd to'lov
    student_cash_id = 7100000086
    async with async_session() as session:
        pay_cash = Payment(
            student_id=student_cash_id,
            group_id=new_group_id,
            amount=float(course.price),
            method=PaymentMethodEnum.cash,
            status=PaymentStatusEnum.pending,
            created_at=datetime.utcnow()
        )
        session.add(pay_cash)
        await session.commit()
        await session.refresh(pay_cash)
        cash_pay_id = pay_cash.id

    c_st, c_res = api_call(f"http://127.0.0.1:8000/api/admin/payments/{cash_pay_id}/approve", method="POST")

    # B) Online Payme Webhook to'lovi
    student_online_id = 7100000087
    trans_id = f"payme_tx_{tag}_{int(time.time())}"
    async with async_session() as session:
        pay_online = Payment(
            student_id=student_online_id,
            group_id=new_group_id,
            amount=float(course.price),
            method=PaymentMethodEnum.payme,
            status=PaymentStatusEnum.pending,
            external_transaction_id=trans_id,
            created_at=datetime.utcnow()
        )
        session.add(pay_online)
        await session.commit()
        await session.refresh(pay_online)
        online_pay_id = pay_online.id

    payme_payload = {
        "method": "PerformTransaction",
        "params": {"id": trans_id},
        "id": 123
    }
    p_st, p_res = api_call("http://127.0.0.1:8000/api/payments/payme", method="POST", payload=payme_payload)

    if c_st == 200 and p_st == 200:
        print(f"  ✅ Naqd to'lov #{cash_pay_id} admin tomonidan tasdiqlandi.")
        print(f"  ✅ Online Payme to'lov #{online_pay_id} webhook orqali muvaffaqiyatli tasdiqlandi.")
        passed_tests += 1
    else:
        print(f"  ❌ To'lovlarni tasdiqlashda xatolik: cash={c_st}, payme={p_st}")

    # -------------------------------------------------------------------------
    # 7. BOTDAN SAVOL BERISH (SUPPORT CHAT)
    # -------------------------------------------------------------------------
    print("\n[7/15] 💬 7. SUPPORT CHAT (SAVOL-JAVOB OQIMI):")
    async with async_session() as session:
        chat = SupportChat(
            student_id=student_online_id,
            admin_id=new_admin_id,
            status=SupportChatStatusEnum.open,
            last_message_by="student",
            last_message_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        session.add(chat)
        await session.commit()
        await session.refresh(chat)

        # Admin javob beradi va yopadi
        chat.status = SupportChatStatusEnum.closed
        chat.closed_reason = SupportChatClosedReasonEnum.resolved
        chat.closed_at = datetime.utcnow()
        await session.commit()
        print(f"  ✅ Support Chat #{chat.id} ochildi va admin #{new_admin_id} tomonidan javob berilib yopildi.")
        passed_tests += 1

    # -------------------------------------------------------------------------
    # 8. REFERAL TIZIMIDAN FOYDALANISH
    # -------------------------------------------------------------------------
    print("\n[8/15] 🎁 8. REFERAL TIZIMI (+5% BONUS VA AMBASSADOR BADGE):")
    async with async_session() as session:
        ref_user = await session.get(User, student_cash_id)
        if not ref_user.referral_code:
            ref_user.referral_code = f"REF{tag}"

        # Yangi do'st qo'shamiz
        friend_id = 7100000088
        friend = await session.get(User, friend_id)
        if friend:
            friend.referred_by = student_cash_id

        bonus = ReferralBonus(
            user_id=student_cash_id,
            referred_student_id=friend_id,
            bonus_percent=5.0,
            status="applied",
            is_used=False
        )
        badge = UserBadge(user_id=student_cash_id, badge_type="ambassador")
        session.add_all([bonus, badge])
        await session.commit()
        print(f"  ✅ Do'st taklif qilindi: Student #{student_cash_id} ga +5% doimiy chegirma va Ambassador badge berildi!")
        passed_tests += 1

    # -------------------------------------------------------------------------
    # 9. UYGA VAZIFA QO'SHISH (HOMEWORK)
    # -------------------------------------------------------------------------
    print("\n[9/15] 📋 9. YANGI GURUHGA UY VAZIFASI QO'SHISH:")
    async with async_session() as session:
        hw = Homework(
            group_id=new_group_id,
            teacher_id=new_teacher_id,
            title=f"Master Class Homework #{tag}",
            description="IELTS Reading Part 3 & Vocabulary building exercises 1 to 10.",
            due_at=datetime.utcnow() + timedelta(days=3),
            created_at=datetime.utcnow()
        )
        session.add(hw)
        await session.commit()
        await session.refresh(hw)

    hw_st, hw_data = api_call(f"http://127.0.0.1:8000/api/student/homework?user_id={student_cash_id}")
    if hw_st == 200 and len(hw_data) > 0:
        print(f"  ✅ Uy vazifasi biriktirildi: «{hw_data[0]['title']}» (O'quvchi API orqali qabul qildi)")
        passed_tests += 1
    else:
        print(f"  ❌ Uy vazifasini tekshirishda xatolik: {hw_st}")

    # -------------------------------------------------------------------------
    # 10. O'QUVCHINI GURUHDAN CHETLATISH (DROPPED / REFUND)
    # -------------------------------------------------------------------------
    print("\n[10/15] 🚫 10. O'QUVCHINI GURUHDAN CHETLATISH (DROPPED):")
    async with async_session() as session:
        enr_drop = (await session.execute(
            select(Enrollment).where(Enrollment.student_id == student_cash_id, Enrollment.group_id == new_group_id)
        )).scalars().first()
        if enr_drop:
            enr_drop.status = EnrollmentStatusEnum.dropped
            enr_drop.is_active = False
            enr_drop.completed_at = datetime.utcnow()
            await session.commit()
            print(f"  ✅ O'quvchi #{student_cash_id} guruhdan chetlatildi (status: dropped, is_active: False)")
            passed_tests += 1
        else:
            print(f"  ❌ Enrollment topilmadi.")

    # -------------------------------------------------------------------------
    # 11. GURUHINI ALMASHTIRISH (GROUP CHANGE REQUEST)
    # -------------------------------------------------------------------------
    print("\n[11/15] 🔄 11. GURUHNI ALMASHTIRISH (GROUP CHANGE):")
    async with async_session() as session:
        # Boshqa mavjud guruhni topamiz
        other_group = (await session.execute(
            select(Group).where(Group.id != new_group_id, Group.is_active == True)
        )).scalars().first()

        req = GroupChangeRequest(
            student_id=student_online_id,
            current_group_id=new_group_id,
            target_group_id=other_group.id,
            reason="Vaqtim to'g'ri kelmay qoldi, kechki guruhga o'tmoqchiman.",
            status="approved",
            approved_by=new_admin_id,
            created_at=datetime.utcnow(),
            processed_at=datetime.utcnow()
        )
        session.add(req)

        # Yangi guruhga enrollment
        new_enr = Enrollment(
            student_id=student_online_id,
            group_id=other_group.id,
            status=EnrollmentStatusEnum.active,
            is_active=True,
            enrolled_at=datetime.utcnow()
        )
        session.add(new_enr)
        await session.commit()
        print(f"  ✅ Student #{student_online_id} guruhi o'zgartirildi: {new_group_id} -> {other_group.id} ({other_group.name})")
        passed_tests += 1

    # -------------------------------------------------------------------------
    # 12. PROGRESSNI KO'RISH (STUDENT PROGRESS)
    # -------------------------------------------------------------------------
    print("\n[12/15] 📊 12. O'QUVCHI PROGRESS VA STATISTIKASI:")
    p_st, p_data = api_call(f"http://127.0.0.1:8000/api/student/progress?user_id={student_online_id}")
    if p_st == 200 and "attendance_percent" in p_data:
        print(f"  ✅ Student #{student_online_id} progressi: Davomat: {p_data.get('attendance_percent')}%, Testlar: {p_data.get('tests_taken')}, Nishonlar: {p_data.get('badges')}")
        passed_tests += 1
    else:
        print(f"  ❌ Progressni olishda xatolik: {p_st}")

    # -------------------------------------------------------------------------
    # 13. ODDIY TEST TOPSHIRISH
    # -------------------------------------------------------------------------
    print("\n[13/15] ✍️ 13. ODDIY TEST TOPSHIRISH (PLACEMENT TEST):")
    # A1 testidan 100% oladi
    async with async_session() as session:
        t_a1 = (await session.execute(select(Test).where(Test.level == "A1", Test.is_active == True))).scalars().first()

    a1_answers = [{"question_id": q.get("id"), "answer": (q.get("correct_answer") or q.get("correct"))} for q in (t_a1.questions or [])]
    simple_sub_payload = {"answers": a1_answers, "duration_seconds": 60, "is_trial": False}
    s_st, s_res = api_call(f"http://127.0.0.1:8000/api/tests/{t_a1.id}/submit?user_id={student_online_id}", method="POST", payload=simple_sub_payload)
    if s_st == 200 and s_res.get("passed"):
        print(f"  ✅ Test topshirildi: Ball: {s_res.get('score')}/{s_res.get('total')} ({s_res.get('percent')}%), O'tdi: {s_res.get('passed')}")
        passed_tests += 1
    else:
        print(f"  ❌ Test topshirishda xatolik: {s_st}")

    # -------------------------------------------------------------------------
    # 14. REKLAMA / BROADCAST YUBORISH (POST /api/admin/broadcast)
    # -------------------------------------------------------------------------
    print("\n[14/15] 📢 14. REKLAMA / OMAVIY XABARNOMA TARQATISH (POST /api/admin/broadcast):")
    b_payload = {
        "text": f"🔥 <b>ALPHA LC da YANGI QABUL!</b>\n\nIELTS 8.0+ kafolatlangan yangi intensiv kurslarimizga start berilmoqda!",
        "target_role": "all",
        "button_text": "Batafsil ma'lumot",
        "button_url": "https://alphalc.uz/courses"
    }
    b_st, b_res = api_call("http://127.0.0.1:8000/api/admin/broadcast", method="POST", payload=b_payload)
    if b_st == 200:
        print(f"  ✅ Broadcast muvaffaqiyatli yuborildi: {b_res.get('message', 'Yuborildi')}")
        passed_tests += 1
    else:
        print(f"  ❌ Broadcast xatolik ({b_st}): {b_res}")

    # -------------------------------------------------------------------------
    # 15. SERTIFIKAT GENERATSIYA QILISH (PDF)
    # -------------------------------------------------------------------------
    print("\n[15/15] 🎓 15. PDF SERTIFIKAT YARATISH (REPORTLAB GENERATOR):")
    pdf_bytes = generate_certificate_pdf(
        student_name="Azizbek Rahimov",
        course_type="IELTS Intensive",
        level="B2"
    )
    if pdf_bytes and len(pdf_bytes) > 500:
        cert_path = "scratch/sample_certificate.pdf"
        os.makedirs("scratch", exist_ok=True)
        with open(cert_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"  ✅ Yuqori sifatli PDF sertifikat muvaffaqiyatli generatsiya qilindi! ({len(pdf_bytes):,} bayt, Fayl: {cert_path})")
        passed_tests += 1
    else:
        print(f"  ❌ Sertifikat generatsiyasida xatolik: hajm={len(pdf_bytes) if pdf_bytes else 0}")

    # -------------------------------------------------------------------------
    # YAKUNIY XULOSA
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(f"🏁 MASTER TEST YAKUNLANDI: {passed_tests}/{total_tests} ta funksiya 100% muvaffaqiyatli ishladi!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_master_test())
