"""
ALPHA LC — 100 ta sinov hisoblaridan real HTTP so'rovlar yuborish simulyatori.
Ushbu skript:
1. O'qituvchilar nomidan (Teachers 7100000001 - 7100000005)
2. Har xil sinov o'quvchilari nomidan (Students 7100000006 - 7100000100)
FastAPI backendiga haqiqiy HTTP so'rovlarini jo'natadi:
- O'qituvchi rollari va kabineti (/api/teacher/...)
- O'quvchi progressi va natijalari (/api/student/progress)
- Daraja testlarini topshirish (/api/tests/submit)
- Sinov darsi arizalarini jo'natish (is_trial=True)
- Kurslar katalogi va Admin hisobotlari
"""
import sys
import os
import json
import random
import urllib.request
import asyncio

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import select
from backend.database import async_session
from backend.models import User, RoleEnum, Test, Group


def send_http(url: str, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "AlphaLC-TestBot/2.0"},
        method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
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


async def main():
    print("=" * 75)
    print("🚀 FAKE AKKAUNTLARDAN FASTAPI SERVERGA SO'ROVLAR YUBORISH")
    print("=" * 75)

    # 1. Bazadan fake akkauntlarni olish
    async with async_session() as session:
        teachers = (await session.execute(
            select(User).where(User.role == RoleEnum.teacher, User.id >= 7100000001, User.id <= 7100000100)
        )).scalars().all()

        students = (await session.execute(
            select(User).where(User.role == RoleEnum.student, User.id >= 7100000001, User.id <= 7100000100)
        )).scalars().all()

        tests = (await session.execute(
            select(Test).where(Test.is_active == True)
        )).scalars().all()
        db_test_map = {
            t.id: {str(q.get("id") or f"q_{idx+1}"): (q.get("correct_answer") or q.get("correct")) for idx, q in enumerate(t.questions or [])}
            for t in tests
        }

    if not teachers or not students:
        print("❌ Fake hisoblar topilmadi! Avval 'python seed_100_test_accounts.py' ni bajaring.")
        return

    print(f"📋 Aniqlangan akkauntlar: {len(teachers)} ta O'qituvchi, {len(students)} ta O'quvchi")
    print("-" * 75)

    req_count = 0
    success_count = 0

    # -------------------------------------------------------------
    # 1. TEACHER SO'ROVLARI (O'qituvchilar profili va kabineti)
    # -------------------------------------------------------------
    print("\n👨‍🏫 1. O'QITUVCHILAR NOMIDAN SO'ROVLAR:")
    for t in teachers:
        req_count += 1
        url = f"http://127.0.0.1:8000/api/teacher/user-roles?user_id={t.id}"
        st, res = send_http(url)
        if st == 200:
            success_count += 1
            print(f"  [GET] {t.full_name} (#{t.id}) -> Roles: is_teacher={res.get('is_teacher')}, is_admin={res.get('is_admin')}")
        else:
            print(f"  [ERR] {t.full_name} (#{t.id}) -> Status: {st}")

        # O'qituvchi workspace
        req_count += 1
        w_url = f"http://127.0.0.1:8000/api/teacher/workspace?user_id={t.id}"
        w_st, w_res = send_http(w_url)
        if w_st == 200:
            success_count += 1
            print(f"  [GET] {t.full_name} Workspace -> Guruhlar: {len(w_res.get('groups', []))}, Talabalar: {w_res.get('total_students_count', 0)}")
        else:
            print(f"  [ERR] {t.full_name} Workspace -> Status: {w_st}")

    # -------------------------------------------------------------
    # 2. STUDENT PROGRESS SO'ROVLARI (O'quvchilar progressi)
    # -------------------------------------------------------------
    print("\n🎓 2. O'QUVCHILAR PROGRESSI VA STATISTIKASI:")
    # 15 ta turli xil o'quvchilarni tanlaymiz
    sample_students = random.sample(students, min(15, len(students)))
    for s in sample_students:
        req_count += 1
        url = f"http://127.0.0.1:8000/api/student/progress?user_id={s.id}"
        st, res = send_http(url)
        if st == 200:
            success_count += 1
            badges = res.get('badges', [])
            b_str = ", ".join(badges) if badges else "yo'q"
            print(f"  [GET] O'quvchi: {s.full_name} (#{s.id}) -> Davomat: {res.get('attendance_percent')}%, O'rtacha ball: {res.get('average_test_score')}, Nishonlar: [{b_str}]")
        else:
            print(f"  [ERR] O'quvchi: {s.full_name} (#{s.id}) -> Status: {st}")

    # -------------------------------------------------------------
    # 3. TEST TOPSHIRISH SO'ROVLARI (Placement testlar)
    # -------------------------------------------------------------
    print("\n✍️ 3. O'QUVCHILAR TEST TOPSHIRISHI VA FREE DARS ARIZALARI:")
    # Har xil darajadagi testlarni yechish uchun 10 ta yangi o'quvchini olamiz
    active_test_students = random.sample(students, min(10, len(students)))

    # Mavjud A1-C2 testlaridan bittasini olamiz
    test_levels = ["A1", "A2", "B1", "B2", "C1"]
    for idx, s in enumerate(active_test_students):
        lvl = random.choice(test_levels)
        req_count += 1
        # 1. Test savollarini olish
        t_url = f"http://127.0.0.1:8000/api/tests/by-level/{lvl}?user_id={s.id}"
        t_st, t_data = send_http(t_url)

        if t_st == 200 and "questions" in t_data and len(t_data["questions"]) > 0:
            success_count += 1
            questions = t_data["questions"]
            test_id = t_data.get("id", 1)
            corr_map = db_test_map.get(test_id, {})

            # Har bir o'quvchining qobiliyatini belgilaymiz (kuchli, o'rtacha, zaif)
            student_ability = random.choices(["high", "mid", "low"], weights=[0.5, 0.3, 0.2])[0]
            answers = []
            for q in questions:
                corr = corr_map.get(q["id"])
                opts = q.get("options", [])
                
                if student_ability == "high":
                    # 90% to'g'ri
                    ans = corr if (corr and random.random() < 0.90) else (random.choice(opts) if opts else "A")
                elif student_ability == "mid":
                    # 70% to'g'ri
                    ans = corr if (corr and random.random() < 0.70) else (random.choice(opts) if opts else "A")
                else:
                    # 30% to'g'ri (o'ta olmaslik)
                    ans = corr if (corr and random.random() < 0.30) else (random.choice(opts) if opts else "A")
                    
                answers.append({"question_id": q["id"], "answer": ans})

            # 2. Test topshirish (har 2 tadan birida Free dars so'rovi is_trial=True)
            is_trial = (idx % 2 == 0)
            sub_payload = {
                "answers": answers,
                "duration_seconds": random.randint(30, 180),
                "is_trial": is_trial
            }
            req_count += 1
            test_id = t_data.get("id", 1)
            sub_url = f"http://127.0.0.1:8000/api/tests/{test_id}/submit?user_id={s.id}"
            sub_st, sub_res = send_http(sub_url, method="POST", payload=sub_payload)

            if sub_st == 200:
                success_count += 1
                trial_tag = " [FREE DARS ARIZASI BILAN]" if is_trial else ""
                print(f"  [POST] {s.full_name} (#{s.id}) -> Test {lvl}: {sub_res.get('score')}/{sub_res.get('total')} ({sub_res.get('percent')}%), O'tdi: {sub_res.get('passed')}{trial_tag}")
            else:
                print(f"  [ERR] {s.full_name} Test topshirishda xatolik: {sub_st}")
        else:
            print(f"  [ERR] {lvl} testini olishda xatolik: {t_st}")

    # -------------------------------------------------------------
    # 4. KURS VA ADMIN MA'LUMOTLARI
    # -------------------------------------------------------------
    print("\n📚 4. KURSLAR VA ADMIN STATISTIKASI:")
    req_count += 1
    c_st, c_data = send_http("http://127.0.0.1:8000/api/courses")
    if c_st == 200:
        success_count += 1
        print(f"  [GET] /api/courses -> {len(c_data)} ta kurs ma'lumotlari olindi.")

    req_count += 1
    d_st, d_data = send_http("http://127.0.0.1:8000/api/admin/dashboard")
    if d_st == 200:
        success_count += 1
        print(f"  [GET] /api/admin/dashboard -> Jami talabalar: {d_data.get('total_students')}, Faol guruhlar: {d_data.get('active_groups')}")

    print("\n" + "=" * 75)
    print(f"🏁 XULOSA: Jami {success_count}/{req_count} ta so'rov fake akkauntlardan muvaffaqiyatli yuborildi va qayta ishlandi! ({success_count/req_count*100:.1f}%)")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(main())
