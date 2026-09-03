import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from sqlalchemy import select
from backend.database import async_session
from backend.models import User, TestResult, FreeTrialRequest, Test
from backend.services.user_service import get_admin_ids

async def main():
    async with async_session() as s:
        admins = await get_admin_ids()
        print(f"ADMIN IDS: {admins}")

        users = (await s.execute(select(User))).scalars().all()
        print(f"ALL USERS ({len(users)}):")
        for u in users:
            print(f"  User ID: {u.id}, Name: {u.full_name}, Username: {u.username}, Role: {u.role.value}")

        tr_list = (await s.execute(select(TestResult).order_by(TestResult.created_at.desc()).limit(10))).scalars().all()
        print(f"\nTEST RESULTS ({len(tr_list)}):")
        for tr in tr_list:
            print(f"  Result ID: {tr.id}, Student ID: {tr.student_id}, Test ID: {tr.test_id}, Score: {tr.score}, Passed: {tr.passed}, At: {tr.created_at}")

        enrs = (await s.execute(select(Enrollment))).scalars().all()
        print(f"\nENROLLMENTS ({len(enrs)}):")
        for e in enrs:
            print(f"  Enrollment ID: {e.id}, Student ID: {e.student_id}, Group ID: {e.group_id}, Status: {e.status.value}, IsActive: {e.is_active}")

if __name__ == "__main__":
    from backend.models import Enrollment
    asyncio.run(main())
