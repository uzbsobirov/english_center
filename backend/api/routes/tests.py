"""
Test tizimi API'lari.
- GET /api/tests/active - joriy faol testni (savollar, to'g'ri javobsiz) qaytaradi
- POST /api/tests/{test_id}/submit - javoblarni qabul qiladi, ballni hisoblaydi, natijani saqlaydi
  va agar o'tgan bo'lsa, avtomatik ravishda free-dars so'rovini yaratib, o'qituvchilarga xabar beradi
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from pydantic import BaseModel

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from data.config import env
from backend.database import async_session
from backend.models import Test, TestResult, FreeTrialRequest, User, RoleEnum
from backend.deps import get_current_telegram_user

router = APIRouter(prefix="/api/tests", tags=["tests"])

BOT_TOKEN = env.str("BOT_TOKEN")


class AnswerItem(BaseModel):
    question_id: str
    answer: str


class SubmitPayload(BaseModel):
    answers: list[AnswerItem]
    duration_seconds: int | None = None


@router.get("/active")
async def get_active_test(user: dict = Depends(get_current_telegram_user)):
    """
    ESKI endpoint - moslik uchun qoldirilgan, birinchi faol testni qaytaradi.
    Yangi oqimda /by-level/{level} ishlatiladi.
    """
    async with async_session() as session:
        result = await session.execute(
            select(Test).where(Test.is_active == True).limit(1)
        )
        test = result.scalar_one_or_none()

    if test is None:
        raise HTTPException(status_code=404, detail="Faol test topilmadi")

    return _serialize_test(test)


@router.get("/by-level/{level}")
async def get_test_by_level(level: str, user: dict = Depends(get_current_telegram_user)):
    """
    Tanlangan darajaga (A1, A2, B1...) mos faol testni qaytaradi.
    """
    async with async_session() as session:
        result = await session.execute(
            select(Test).where(Test.is_active == True, Test.level == level).limit(1)
        )
        test = result.scalar_one_or_none()

    if test is None:
        raise HTTPException(
            status_code=404,
            detail=f"'{level}' darajasi uchun faol test topilmadi",
        )

    return _serialize_test(test)


def _serialize_test(test: Test) -> dict:
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

async def _notify_teachers_about_trial(trial_request_id: int, student_name: str, level: str):
    """
    Barcha o'qituvchilarga free-dars so'rovi haqida xabar yuboradi,
    'Qabul qilish' tugmasi bilan. Birinchi bosgan oladi (7.1.1).
    """
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.role == RoleEnum.teacher, User.is_active == True)
        )
        teachers = result.scalars().all()

    if not teachers:
        return

    bot = Bot(token=BOT_TOKEN)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="✅ Qabul qilish",
                callback_data=f"trial_accept:{trial_request_id}",
            )
        ]]
    )
    text = (
        f"🆕 Yangi free-dars so'rovi!\n\n"
        f"O'quvchi: {student_name}\n"
        f"Daraja: {level}\n\n"
        f"Birinchi bo'lib qabul qilgan o'qituvchi ushbu o'quvchiga dars beradi."
    )

    for teacher in teachers:
        try:
            await bot.send_message(teacher.id, text, reply_markup=keyboard)
        except Exception:
            continue

    await bot.session.close()


async def _notify_admins_about_beginner(student_name: str, student_id: int):
    """
    Eng past daraja (A1) testidan ham yiqilgan o'quvchi haqida adminlarga xabar beradi -
    bunday o'quvchi bilan qo'lda bog'lanish va boshlang'ich kurs taklif qilish kerak bo'ladi.
    """
    admin_ids = env.list("ADMINS")
    if not admin_ids:
        return

    bot = Bot(token=BOT_TOKEN)
    text = (
        f"⚠️ Diqqat: o'quvchi eng boshlang'ich (A1) testidan ham o'ta olmadi.\n\n"
        f"Ism: {student_name}\n"
        f"Telegram ID: {student_id}\n\n"
        f"Iltimos, qo'lda bog'lanib, boshlang'ich kurs haqida ma'lumot bering."
    )
    for admin_id in admin_ids:
        try:
            await bot.send_message(int(admin_id), text)
        except Exception:
            continue
    await bot.session.close()


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
        await session.flush()

        trial_request = None
        if passed:
            trial_request = FreeTrialRequest(
                student_id=user["id"],
                test_result_id=test_result.id,
            )
            session.add(trial_request)
            await session.flush()

        await session.commit()

        # Natija turini aniqlaymiz - frontend shunga qarab xabar ko'rsatadi
        outcome = "passed"
        if not passed:
            if test.level.value == "A1":
                outcome = "beginner_recommended"
            else:
                outcome = "try_lower_level"

        if trial_request is not None:
            student_name = user.get("first_name", "Noma'lum")
            await _notify_teachers_about_trial(
                trial_request.id, student_name, test.level.value
            )
        elif outcome == "beginner_recommended":
            student_name = user.get("first_name", "Noma'lum")
            await _notify_admins_about_beginner(student_name, user["id"])

        return {
            "score": correct_count,
            "total": total,
            "percent": round(percent, 1),
            "passed": passed,
            "outcome": outcome,
            "free_trial_created": trial_request is not None,
        }