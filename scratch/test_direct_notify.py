import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from sqlalchemy import select
from backend.database import async_session
from backend.models import User, Test, TestResult
from backend.api.routes.tests import _send_test_notifications

async def test_notify():
    async with async_session() as s:
        test = (await s.execute(select(Test).limit(1))).scalars().first()
        user = await s.get(User, 1435473812)
        print(f"Testing notification for User: {user.full_name}, ID: {user.id}, Test: {test.title}")

    await _send_test_notifications(
        student_id=user.id,
        student_name=user.full_name,
        student_username=user.username,
        student_phone=user.phone,
        test=test,
        score=3,
        total=3,
        percent=100.0,
        passed=True,
        trial_id=1,
    )
    print("Notification function completed!")

if __name__ == "__main__":
    asyncio.run(test_notify())
