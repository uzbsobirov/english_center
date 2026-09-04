import sys
import json
import asyncio
import urllib.request
from sqlalchemy import select

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.database import async_session
from backend.models import User, Course, Group, Test, TestResult, FreeTrialRequest, SupportChat


def test_api_endpoint(url: str, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(payload).encode() if payload else None
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
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


async def run_all_tests():
    print("=" * 60)
    print("🚀 BOT VA WEB APP TIZIMINI TO'LIQ TESTDAN O'TKAZISH")
    print("=" * 60)
    
    passed_count = 0
    total_count = 0

    # 1. API: Kurslar ro'yxati
    total_count += 1
    status, data = test_api_endpoint("http://127.0.0.1:8000/api/courses")
    if status == 200 and isinstance(data, list):
        print(f"✅ 1. GET /api/courses -> Muvaffaqiyatli ({len(data)} ta kurs topildi)")
        passed_count += 1
    else:
        print(f"❌ 1. GET /api/courses -> Xatolik ({status}): {data}")

    # 2. API: Barcha darajalar bo'yicha testlar (A1-C2)
    for lvl in ["A1", "A2", "B1", "B2", "C1", "C2"]:
        total_count += 1
        status, data = test_api_endpoint(f"http://127.0.0.1:8000/api/tests/by-level/{lvl}")
        if status == 200 and "questions" in data and len(data["questions"]) > 0:
            print(f"✅ 2. GET /api/tests/by-level/{lvl} -> Muvaffaqiyatli ({len(data['questions'])} ta savol)")
            passed_count += 1
        else:
            print(f"❌ 2. GET /api/tests/by-level/{lvl} -> Xatolik ({status}): {data}")

    # 3. API: Test topshirish (Submit test)
    total_count += 1
    a1_status, a1_data = test_api_endpoint("http://127.0.0.1:8000/api/tests/by-level/A1")
    a1_id = a1_data.get("id", 2)
    answers = []
    for q in a1_data.get("questions", [])[:3]:
        corr = q.get("correct") or q.get("correct_answer")
        if not corr and "options" in q and len(q["options"]) > 0:
            corr = q["options"][0]
        answers.append({"question_id": q["id"], "answer": corr})

    submit_payload = {
        "answers": answers,
        "duration_seconds": 30,
    }
    # Fake test student ID ishlatamiz (shaxsiy akkaunt o'rniga)
    test_fake_student_id = 7100000010
    status, data = test_api_endpoint(f"http://127.0.0.1:8000/api/tests/{a1_id}/submit?user_id={test_fake_student_id}", method="POST", payload=submit_payload)
    if status == 200 and "score" in data:
        print(f"✅ 3. POST /api/tests/{a1_id}/submit -> Muvaffaqiyatli (Score: {data['score']}/{data['total']}, Passed: {data['passed']})")
        passed_count += 1
    else:
        print(f"❌ 3. POST /api/tests/{a1_id}/submit -> Xatolik ({status}): {data}")

    # 4. API: Admin Dashboard statistikasi
    total_count += 1
    status, data = test_api_endpoint("http://127.0.0.1:8000/api/admin/dashboard")
    if status == 200 and "total_students" in data:
        print(f"✅ 4. GET /api/admin/dashboard -> Muvaffaqiyatli (Talabalar: {data['total_students']}, Guruhlar: {data['active_groups']})")
        passed_count += 1
    else:
        print(f"❌ 4. GET /api/admin/dashboard -> Xatolik ({status}): {data}")

    # 5. Database: Admin va User tekshiruvi
    total_count += 1
    async with async_session() as session:
        admin_user = await session.get(User, 1435473812)
        if admin_user and admin_user.role.value in ("admin", "manager"):
            print(f"✅ 5. Database Admin tekshiruvi -> Muvaffaqiyatli (User: {admin_user.full_name}, Role: {admin_user.role.value})")
            passed_count += 1
        else:
            print(f"❌ 5. Database Admin tekshiruvi -> Admin roli topilmadi")

    # 6. Database: Referal tizimi tekshiruvi
    total_count += 1
    async with async_session() as session:
        if admin_user and admin_user.referral_code:
            print(f"✅ 6. Referal tizimi -> Muvaffaqiyatli (Referral code: {admin_user.referral_code})")
            passed_count += 1
        else:
            print(f"❌ 6. Referal tizimi -> Referral code mavjud emas")

    print("=" * 60)
    print(f"📊 XULOSA: {passed_count}/{total_count} ta test muvaffaqiyatli o'tdi ({passed_count/total_count*100:.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
