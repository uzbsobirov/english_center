import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from unittest.mock import AsyncMock
from sqlalchemy import select, delete

from backend.database import async_session
from backend.models import (
    User, RoleEnum, Group, Course, Test, TestResult, FreeTrialRequest, FreeTrialStatusEnum, LevelEnum
)
from backend.api.routes.tests import submit_test, SubmitPayload, AnswerItem

async def run_trial_flow_test():
    print("--- [TEST] Running Free Trial Flow & Notification Test Suite ---")

    student_id = 999888777
    student_user = {"id": student_id, "first_name": "Test Student", "username": "test_student"}

    async with async_session() as session:
        # Clean
        await session.execute(delete(FreeTrialRequest).where(FreeTrialRequest.student_id == student_id))
        await session.execute(delete(TestResult).where(TestResult.student_id == student_id))
        await session.execute(delete(User).where(User.id == student_id))
        await session.commit()

        # Create student
        student = User(id=student_id, full_name="Test Student", username="test_student", role=RoleEnum.student, phone="+998901234567")
        session.add(student)

        # Get an active test (e.g. CEFR A1)
        test_res = await session.execute(select(Test).where(Test.level == LevelEnum.A1).limit(1))
        test = test_res.scalars().first()
        test_id = test.id
        q_list = test.questions
        await session.commit()

    # Create correct answers payload
    answers = [AnswerItem(question_id=q["id"], answer=q["correct_answer"]) for q in q_list]
    payload = SubmitPayload(answers=answers, duration_seconds=45, is_trial=True)

    # Call submit_test
    res = await submit_test(test_id=test_id, payload=payload, user=student_user)
    assert res["passed"] == True
    print(f"[OK] submit_test result: score={res['score']}/{res['total']}, percent={res['percent']}%, passed={res['passed']}")

    # Verify FreeTrialRequest was created in DB
    async with async_session() as session:
        trial_res = await session.execute(
            select(FreeTrialRequest).where(FreeTrialRequest.student_id == student_id)
        )
        trial = trial_res.scalars().first()
        assert trial is not None, "FreeTrialRequest was NOT created in DB!"
        assert trial.status == FreeTrialStatusEnum.pending
        print(f"[OK] FreeTrialRequest created: ID={trial.id}, status={trial.status.value}, student_id={trial.student_id}")

        # Simulate teacher accepting the trial
        teacher_id = 1435473812
        trial.status = FreeTrialStatusEnum.invited
        trial.teacher_id = teacher_id
        await session.commit()

        # Check updated
        updated_trial = await session.get(FreeTrialRequest, trial.id)
        assert updated_trial.status == FreeTrialStatusEnum.invited
        assert updated_trial.teacher_id == teacher_id
        print(f"[OK] Teacher accepted trial: status={updated_trial.status.value}, teacher_id={updated_trial.teacher_id}")

        # Cleanup
        await session.execute(delete(FreeTrialRequest).where(FreeTrialRequest.student_id == student_id))
        await session.execute(delete(TestResult).where(TestResult.student_id == student_id))
        await session.execute(delete(User).where(User.id == student_id))
        await session.commit()
        print("[OK] Test database cleaned up.")

    print("--- [ALL FREE TRIAL FLOW TESTS PASSED] ---")

if __name__ == "__main__":
    asyncio.run(run_trial_flow_test())
