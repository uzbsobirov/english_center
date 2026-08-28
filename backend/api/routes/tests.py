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

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from backend.services.user_service import get_admin_ids, get_teacher_ids


async def _notify_teachers_about_trial(trial_request_id: int, student_name: str, student_id: int, level: str, score_percent: float):
    """
    Barcha o'qituvchi va adminlarga free-dars so'rovi haqida xabar yuboradi,
    'Qabul qilish' tugmasi bilan (7.1.1).
    """
    teacher_ids = await get_teacher_ids(level=level)
    admin_ids = await get_admin_ids()
    target_ids = list(set(teacher_ids + admin_ids))

    if not target_ids:
        return

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="✅ Free Darsni Qabul Qilish",
                callback_data=f"trial_accept:{trial_request_id}",
            )
        ]]
    )
    student_link_str = f"<a href='tg://user?id={student_id}'>{student_name}</a>"
    text = (
        f"🎉 <b>Yangi Free-Dars So'rovi!</b>\n\n"
        f"👤 <b>O'quvchi:</b> {student_link_str} (ID: <code>{student_id}</code>)\n"
        f"🎯 <b>Daraja:</b> {level} (Test bali: <b>{score_percent:.1f}%</b>)\n\n"
        f"<i>Birinchi bo'lib qabul qilgan o'qituvchi ushbu o'quvchiga dars beradi.</i>"
    )

    for target_id in target_ids:
        try:
            await bot.send_message(target_id, text, reply_markup=keyboard)
        except Exception:
            continue

    await bot.session.close()


async def _notify_admins_about_test_submission(
    student_id: int,
    student_name: str,
    test_level: str,
    cert_type: str,
    score: int,
    total: int,
    percent: float,
    passed: bool,
):
    """
    Har qanday test topshirilganda adminlar va o'qituvchilarga xabarnoma yuboradi.
    """
    admin_ids = await get_admin_ids()
    teacher_ids = await get_teacher_ids(level=test_level)
    target_ids = list(set(admin_ids + teacher_ids))

    if not target_ids:
        return

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    status_icon = "✅ Muvaffaqiyatli o'tdi" if passed else "❌ O'ta olmadi"
    student_link_str = f"<a href='tg://user?id={student_id}'>{student_name}</a>"
    text = (
        f"📊 <b>Yangi Test Topshirildi!</b>\n\n"
        f"👤 <b>O'quvchi:</b> {student_link_str} (ID: <code>{student_id}</code>)\n"
        f"🎯 <b>Yo'nalish:</b> {cert_type} ({test_level})\n"
        f"📈 <b>To'plagan bali:</b> {score}/{total} (<b>{percent:.1f}%</b>)\n"
        f"📌 <b>Natija:</b> {status_icon}"
    )
    for target_id in target_ids:
        try:
            await bot.send_message(target_id, text)
        except Exception:
            continue
    await bot.session.close()


async def _notify_admins_about_beginner(student_name: str, student_id: int):
    """
    Eng past daraja (A1) testidan ham yiqilgan o'quvchi haqida adminlarga xabar beradi (TZ 18).
    """
    admin_ids = await get_admin_ids()
    if not admin_ids:
        return

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    student_link_str = f"<a href='tg://user?id={student_id}'>{student_name}</a>"
    text = (
        f"⚠️ <b>Diqqat:</b> O'quvchi eng boshlang'ich (A1) testidan o'ta olmadi.\n\n"
        f"👤 <b>Ism:</b> {student_link_str}\n"
        f"🆔 <b>Telegram ID:</b> <code>{student_id}</code>\n\n"
        f"<i>Iltimos, o'quvchi bilan bog'lanib, boshlang'ich guruh haqida ma'lumot bering.</i>"
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

        # O'quvchi ismini bazadan olamiz (agar bor bo'lsa)
        db_user = await session.get(User, user["id"])
        if db_user and db_user.full_name:
            student_name = db_user.full_name
        else:
            student_name = user.get("first_name", "Noma'lum")
            if user.get("last_name"):
                student_name += f" {user['last_name']}"

        cert_type = str(getattr(test, "certificate_type", "General"))

        # 1. Barcha test topshirishlar haqida admin va o'qituvchilarga xabar beramiz
        try:
            await _notify_admins_about_test_submission(
                student_id=user["id"],
                student_name=student_name,
                test_level=test.level.value,
                cert_type=cert_type,
                score=correct_count,
                total=total,
                percent=percent,
                passed=passed,
            )

            # 2. Agar o'tgan bo'lsa - Free trial accept so'rovi
            if trial_request is not None:
                await _notify_teachers_about_trial(
                    trial_request.id, student_name, user["id"], test.level.value, percent
                )
            elif outcome == "beginner_recommended":
                await _notify_admins_about_beginner(student_name, user["id"])
        except Exception as e:
            print(f"⚠️ Test submission notification error: {e}")

        return {
            "score": correct_count,
            "total": total,
            "percent": round(percent, 1),
            "passed": passed,
            "outcome": outcome,
            "free_trial_created": trial_request is not None,
        }