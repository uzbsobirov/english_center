"""
ALPHA LC — 100 ta sinov hisoblari bilan tizimni to'liq testdan o'tkazish skripti.
"""
import sys
import os
import json
import urllib.request
import asyncio

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import select, func
from backend.database import async_session
from backend.models import (
    User, RoleEnum, Enrollment, Payment, Attendance,
    TestResult, FreeTrialRequest, UserBadge, ReferralBonus, Test
)
from backend.services.scheduler import check_trial_attendance_reminders


def test_api(url: str, method: str = "GET", payload: dict | None = None, headers: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(payload).encode() if payload else None
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            raw = res.read().decode()
            return res.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode() if e.fp else ""
        try:
            return e.code, json.loads(raw) if raw else {}
        except Exception:
            return e.code, {"detail": raw}
    except Exception as e:
        return 0, {"error": str(e)}


async def run_tests():
    print("=" * 70)
    print("🧪 100 TA TEST AKKAUNT BILAN TIZIMNI SINASH")
    print("=" * 70)

    passed = 0
    total = 0

    # -------------------------------------------------------------
    # 1. Database Tekshiruvlari
    # -------------------------------------------------------------
    print("\n📦 1. MA'LUMOTLAR BAZASI HOLATI:")
    async with async_session() as session:
        # Userlar soni
        total += 1
        test_users = (await session.execute(
            select(User).where(User.id >= 7100000001, User.id <= 7100000100)
        )).scalars().all()
        if len(test_users) == 100:
            print(f"  ✅ 100 ta test foydalanuvchisi mavjud (ID: 7100000001 - 7100000100)")
            passed += 1
        else:
            print(f"  ❌ Test foydalanuvchilari soni: {len(test_users)} (100 ta kutilgan edi)")

        # Roller taqsimoti
        total += 1
        teachers = [u for u in test_users if u.role == RoleEnum.teacher]
        students = [u for u in test_users if u.role == RoleEnum.student]
        if len(teachers) == 5 and len(students) == 95:
            print(f"  ✅ Rollar to'g'ri taqsimlangan: 5 ta o'qituvchi, 95 ta o'quvchi")
            passed += 1
        else:
            print(f"  ❌ Rollar noto'g'ri: {len(teachers)} teacher, {len(students)} student")

        # Bog'liq jadvallar statistikasi
        enr_cnt = (await session.execute(
            select(func.count(Enrollment.id)).where(Enrollment.student_id >= 7100000001, Enrollment.student_id <= 7100000100)
        )).scalar() or 0

        pay_cnt = (await session.execute(
            select(func.count(Payment.id)).where(Payment.student_id >= 7100000001, Payment.student_id <= 7100000100)
        )).scalar() or 0

        att_cnt = (await session.execute(
            select(func.count(Attendance.id)).where(Attendance.student_id >= 7100000001, Attendance.student_id <= 7100000100)
        )).scalar() or 0

        badge_cnt = (await session.execute(
            select(func.count(UserBadge.id)).where(UserBadge.user_id >= 7100000001, UserBadge.user_id <= 7100000100)
        )).scalar() or 0

        trial_cnt = (await session.execute(
            select(func.count(FreeTrialRequest.id)).where(FreeTrialRequest.student_id >= 7100000001, FreeTrialRequest.student_id <= 7100000100)
        )).scalar() or 0

        total += 1
        if enr_cnt > 0 and pay_cnt > 0 and att_cnt > 0 and badge_cnt > 0 and trial_cnt > 0:
            print(f"  ✅ Bog'liq ma'lumotlar to'liq shakllangan: Enrollments: {enr_cnt}, Payments: {pay_cnt}, Attendances: {att_cnt}, Badges: {badge_cnt}, Trials: {trial_cnt}")
            passed += 1
        else:
            print(f"  ❌ Bog'liq ma'lumotlarda kamchilik bor")

    # -------------------------------------------------------------
    # 2. Admin API Tekshiruvlari
    # -------------------------------------------------------------
    print("\n📊 2. ADMIN DASHBOARD VA STUDENTS API:")
    total += 1
    status, dash_data = test_api("http://127.0.0.1:8000/api/admin/dashboard")
    if status == 200 and "total_students" in dash_data and dash_data["total_students"] >= 95:
        print(f"  ✅ GET /api/admin/dashboard -> Talabalar: {dash_data['total_students']}, Guruhlar: {dash_data['active_groups']}, Daromad: {dash_data.get('total_revenue', 0):,} so'm")
        passed += 1
    else:
        print(f"  ❌ GET /api/admin/dashboard xatolik ({status}): {dash_data}")

    total += 1
    status, students_data = test_api("http://127.0.0.1:8000/api/admin/students")
    if status == 200 and isinstance(students_data, list) and len(students_data) >= 95:
        sample_student = students_data[0]
        print(f"  ✅ GET /api/admin/students -> {len(students_data)} ta o'quvchi ro'yxati qaytdi (Birinchisi: {sample_student.get('full_name')})")
        passed += 1
    else:
        print(f"  ❌ GET /api/admin/students xatolik ({status}): {students_data}")

    # -------------------------------------------------------------
    # 3. Student WebApp API (Progress, Badges, Attendance)
    # -------------------------------------------------------------
    print("\n🎓 3. O'QUVCHI PROGRESSI (STUDENT API):")
    sample_ids = [7100000010, 7100000025, 7100000050]
    for sid in sample_ids:
        total += 1
        status, prog = test_api(f"http://127.0.0.1:8000/api/student/progress?user_id={sid}")
        if status == 200 and "attendance_percent" in prog:
            print(f"  ✅ Student #{sid} Progress -> Davomat: {prog['attendance_percent']}%, O'rtacha ball: {prog['average_test_score']}, Testlar: {prog['tests_taken']}, Nishonlar: {prog['badges']}")
            passed += 1
        else:
            print(f"  ❌ Student #{sid} Progress xatolik ({status}): {prog}")

    # -------------------------------------------------------------
    # 4. Yangi Test Topshirish (Test Submission)
    # -------------------------------------------------------------
    print("\n✍️ 4. TEST TOPSHIRISH JARAYONI:")
    total += 1
    test_submit_user = 7100000088
    # A1 test savollarini olamiz
    status, a1_test = test_api("http://127.0.0.1:8000/api/tests/by-level/A1")
    if status == 200 and "questions" in a1_test and len(a1_test["questions"]) > 0:
        questions = a1_test["questions"]
        answers = []
        for q in questions:
            corr = q.get("correct") or q.get("correct_answer")
            if not corr and "options" in q and len(q["options"]) > 0:
                corr = q["options"][0]
            answers.append({"question_id": q["id"], "answer": corr})

        submit_data = {
            "answers": answers,
            "duration_seconds": 45,
            "is_trial": False
        }
        test_id = a1_test.get("id", 1)
        sub_status, sub_res = test_api(f"http://127.0.0.1:8000/api/tests/{test_id}/submit?user_id={test_submit_user}", method="POST", payload=submit_data)
        if sub_status == 200 and "score" in sub_res:
            print(f"  ✅ Test #{test_id} topshirildi (Student #{test_submit_user}): Ball: {sub_res['score']}/{sub_res['total']} ({sub_res.get('percent', 0)}%), O'tdi: {sub_res['passed']}")
            passed += 1
        else:
            print(f"  ❌ Test topshirish xatolik ({sub_status}): {sub_res}")
    else:
        print(f"  ❌ A1 testini olishda xatolik ({status}): {a1_test}")

    # -------------------------------------------------------------
    # 5. Scheduler & Reminder Xatoligi Tekshiruvi
    # -------------------------------------------------------------
    print("\n⏰ 5. SCHEDULER VA FREE TRIAL UPDATED_AT TEKSHIRUVI:")
    total += 1
    try:
        class DummyBot:
            async def send_message(self, *args, **kwargs):
                pass

        # check_trial_attendance_reminders funktsiyasini to'g'ridan-to'g'ri chaqiramiz
        await check_trial_attendance_reminders(DummyBot())
        print(f"  ✅ check_trial_attendance_reminders xatosiz va FreeTrialRequest.updated_at muvaffaqiyatli ishladi!")
        passed += 1
    except Exception as e:
        print(f"  ❌ Scheduler funktsiyasida xatolik: {e}")

    # -------------------------------------------------------------
    # Xulosa
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"🏁 TEST NATIJALARI: {passed}/{total} ta test muvaffaqiyatli yakunlandi! ({passed/total*100:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())
