"""
Test tizimi API'lari.
- GET /api/tests/active - joriy faol testni (savollar, to'g'ri javobsiz) qaytaradi
- POST /api/tests/{test_id}/submit - javoblarni qabul qiladi, ballni hisoblaydi, natijani saqlaydi
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from pydantic import BaseModel

from backend.database import async_session
from backend.models import Test, TestResult
from backend.deps import get_current_telegram_user

router = APIRouter(prefix="/api/tests", tags=["tests"])


class AnswerItem(BaseModel):
    question_id: str
    answer: str


class SubmitPayload(BaseModel):
    answers: list[AnswerItem]
    duration_seconds: int | None = None


@router.get("/active")
async def get_active_test(user: dict = Depends(get_current_telegram_user)):
    """
    Hozircha eng sodda variant: bazadagi birinchi faol testni qaytaradi.
    Kelajakda daraja/kurs bo'yicha filtr qo'shiladi.
    To'g'ri javoblar frontendga YUBORILMAYDI - faqat savol matni va variantlar.
    """
    async with async_session() as session:
        result = await session.execute(
            select(Test).where(Test.is_active == True).limit(1)
        )
        test = result.scalar_one_or_none()

    if test is None:
        raise HTTPException(status_code=404, detail="Faol test topilmadi")

    safe_questions = [
        {
            "id": q["id"],
            "type": q["type"],
            "text": q["text"],
            "options": q.get("options"),
        }
        for q in test.questions
    ]

    return {
        "id": test.id,
        "title": test.title,
        "level": test.level.value,
        "passing_score": float(test.passing_score),
        "questions": safe_questions,
    }


@router.post("/{test_id}/submit")
async def submit_test(
    test_id: int,
    payload: SubmitPayload,
    user: dict = Depends(get_current_telegram_user),
):
    async with async_session() as session:
        test = await session.get(Test, test_id)
        if test is None:
            raise HTTPException(status_code=404, detail="Test topilmadi")

        correct_map = {q["id"]: q["correct_answer"] for q in test.questions}
        total = len(correct_map)
        correct_count = 0
        answers_detail = []

        for item in payload.answers:
            is_correct = correct_map.get(item.question_id) == item.answer
            if is_correct:
                correct_count += 1
            answers_detail.append({
                "question_id": item.question_id,
                "answer": item.answer,
                "is_correct": is_correct,
            })

        percent = (correct_count / total * 100) if total else 0
        passed = percent >= float(test.passing_score)

        test_result = TestResult(
            student_id=user["id"],
            test_id=test.id,
            score=correct_count,
            percent=percent,
            passed=passed,
            duration_seconds=payload.duration_seconds,
            answers=answers_detail,
        )
        session.add(test_result)
        await session.commit()

        return {
            "score": correct_count,
            "total": total,
            "percent": round(percent, 1),
            "passed": passed,
        }