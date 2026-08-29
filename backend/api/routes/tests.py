"""
Test tizimi API'lari.
- GET /api/tests/active - joriy faol testni (savollar, to'g'ri javobsiz) qaytaradi
- POST /api/tests/{test_id}/submit - javoblarni qabul qiladi, ballni hisoblaydi, natijani saqlaydi
  va agar o'tgan bo'lsa, avtomatik ravishda free-dars so'rovini yaratib, o'qituvchilarga xabar beradi
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from pydantic import BaseModel

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from data.config import env
from backend.database import async_session
from backend.models import Test, TestResult, FreeTrialRequest, User, RoleEnum, LanguageEnum
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


@router.get("/types")
async def get_test_types(user: dict = Depends(get_current_telegram_user)):
    """Mavjud test yo'nalishlari (IELTS, CEFR)."""
    return [
        {"id": "CEFR", "name": "CEFR Testlari", "description": "A1 - C2 darajalar bo'yicha grammatika va leksika"},
        {"id": "IELTS", "name": "IELTS Testlari", "description": "Academic va General IELTS tayyorgarlik testlari"},
    ]


@router.get("/by-level/{level}")
async def get_test_by_level(
    level: str,
    type: str | None = None,
    user: dict = Depends(get_current_telegram_user)
):
    """
    Tanlangan daraja va yo'nalishga (IELTS/CEFR) mos faol testni qaytaradi.
    """
    async with async_session() as session:
        query = select(Test).where(Test.is_active == True, Test.level == level)
        if type:
            query = query.where(Test.certificate_type.ilike(type))
        result = await session.execute(query.limit(1))
        test = result.scalar_one_or_none()

        # Agar tanlangan yo'nalishda topilmasa, shu darajadagi boshqa faol testga fallback
        if test is None and type:
            result = await session.execute(
                select(Test).where(Test.is_active == True, Test.level == level).limit(1)
            )
            test = result.scalar_one_or_none()

    if test is None:
        raise HTTPException(
            status_code=404,
            detail=f"'{level}' ({type or 'Barcha'}) darajasi uchun faol test topilmadi",
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
        "certificate_type": test.certificate_type,
        "passing_score": float(test.passing_score),
        "questions": safe_questions,
    }


from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from backend.services.user_service import get_admin_ids, get_teacher_ids
from backend.models import Enrollment, Group


async def _send_test_notifications(
    student_id: int,
    student_name: str,
    student_username: str | None,
    test: Test,
    score: int,
    total: int,
    percent: float,
    passed: bool,
):
    """
    Test topshirilganda:
    1. O'quvchining o'ziga natijani yuboradi.
    2. Agar o'quvchi biror guruhda o'qisa, o'sha guruh o'qituvchisiga xabar beradi.
    3. Adminlarga xabarnoma yuboradi.
    """
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    cert_type = str(getattr(test, "certificate_type", "General"))
    level_str = test.level.value if hasattr(test.level, "value") else str(test.level)
    test_title_str = (
        test.title.get("uz", test.title.get("en", "Test"))
        if isinstance(test.title, dict)
        else str(test.title)
    )
    status_icon = "✅ Muvaffaqiyatli o'tdingiz!" if passed else "❌ O'tish balini to'play olmadingiz."

    from aiogram.types import BufferedInputFile
    from backend.services.certificate_generator import generate_certificate_pdf
    from backend.services.gamification import award_badge_if_eligible

    # 1. O'quvchining o'ziga botdan to'g'ridan-to'g'ri xabar
    student_msg = (
        f"📊 <b>Sizning test natijangiz:</b>\n\n"
        f"🎯 <b>Yo'nalish:</b> {cert_type} ({level_str})\n"
        f"📝 <b>Test:</b> {test_title_str}\n"
        f"📈 <b>To'plangan ball:</b> <b>{score}/{total}</b> (<b>{percent:.1f}%</b>)\n"
        f"📌 <b>Holat:</b> {status_icon}"
    )
    try:
        await bot.send_message(student_id, student_msg)
    except Exception as e:
        print(f"⚠️ O'quvchiga xabar yuborishda xatolik ({student_id}): {e}")

    # 2. O'quvchi a'zo bo'lgan guruh o'qituvchisini aniqlaymiz
    notified_teacher_ids = set()
    async with async_session() as session:
        enrollments_res = await session.execute(
            select(Enrollment, Group)
            .join(Group, Enrollment.group_id == Group.id)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.is_active == True,
                Group.is_active == True,
            )
        )
        enrolled_groups = enrollments_res.all()

        # Agar testdan muvaffaqiyatli o'tgan bo'lsa va guruhda o'qisa -> Avtomatik Sertifikat beramiz!
        if passed and enrolled_groups:
            try:
                cert_pdf_bytes = generate_certificate_pdf(
                    student_name=student_name,
                    course_type=cert_type,
                    level=level_str,
                )
                safe_name = student_name.replace(" ", "_")
                cert_file = BufferedInputFile(
                    cert_pdf_bytes,
                    filename=f"Certificate_{safe_name}_{level_str}.pdf",
                )
                await bot.send_document(
                    student_id,
                    cert_file,
                    caption=(
                        f"🎓 <b>Tabriklaymiz, {student_name}!</b>\n\n"
                        f"Siz <b>{cert_type} ({level_str})</b> kursi yakuniy testini "
                        f"<b>{percent:.1f}%</b> ball bilan muvaffaqiyatli topshirdingiz!\n\n"
                        f"Kursni to'liq tamomlaganingiz uchun sizga rasmiy <b>PDF Sertifikat</b> "
                        f"va 🎓 <b>Graduate Badge</b> topshirildi! 🌟\n\n"
                        f"Kelgusi o'qish va faoliyatingizda ulkan zafarlar tilaymiz! 🚀"
                    ),
                )
                await award_badge_if_eligible(student_id, "graduate")

                # Enrollment holatini completed ga o'tkazamiz
                for enr, _ in enrolled_groups:
                    enr.status = EnrollmentStatusEnum.completed
                    enr.completed_at = datetime.utcnow()
                await session.commit()
            except Exception as e:
                print(f"⚠️ Avtomatik sertifikat yuborishda xatolik ({student_id}): {e}")

    student_link = f"<a href='tg://user?id={student_id}'>{student_name}</a>"
    student_user_str = f" (@{student_username})" if student_username else ""

    if enrolled_groups:
        for enrollment, group in enrolled_groups:
            if group.teacher_id and group.teacher_id not in notified_teacher_ids:
                notified_teacher_ids.add(group.teacher_id)
                teacher_msg = (
                    f"📝 <b>Guruhingiz o'quvchisi test topshirdi!</b>\n\n"
                    f"👤 <b>O'quvchi:</b> {student_link}{student_user_str}\n"
                    f"👥 <b>Guruh:</b> <b>{group.name}</b>\n"
                    f"🎯 <b>Test:</b> {cert_type} — {level_str}\n"
                    f"📊 <b>Natija:</b> <b>{score}/{total}</b> (<b>{percent:.1f}%</b>)\n"
                    f"📌 <b>Holat:</b> {'✅ O\'tdi (🎓 Avtomatik Sertifikat berildi)' if passed else '❌ O\'ta olmadi'}"
                )
                try:
                    await bot.send_message(group.teacher_id, teacher_msg)
                except Exception as e:
                    print(f"⚠️ O'qituvchiga xabar yuborishda xatolik ({group.teacher_id}): {e}")

    # 3. Adminlarga xabar
    admin_ids = await get_admin_ids()
    for admin_id in admin_ids:
        if admin_id in notified_teacher_ids or admin_id == student_id:
            continue
        admin_msg = (
            f"📊 <b>Yangi test topshirildi:</b>\n\n"
            f"👤 <b>O'quvchi:</b> {student_link}{student_user_str} (ID: <code>{student_id}</code>)\n"
            f"🎯 <b>Test:</b> {cert_type} ({level_str})\n"
            f"📈 <b>To'plagan bali:</b> <b>{score}/{total}</b> (<b>{percent:.1f}%</b>)\n"
            f"📌 <b>Holat:</b> {'✅ O\'tdi (🎓 Avtomatik Sertifikat berildi)' if passed else '❌ O\'ta olmadi'}"
        )
        try:
            await bot.send_message(int(admin_id), admin_msg)
        except Exception:
            pass


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

        # 1. Avval foydalanuvchini bazada borligini tekshiramiz yoki yaratamiz
        db_user = await session.get(User, user["id"])
        if not db_user:
            name_parts = [user.get("first_name", ""), user.get("last_name", "")]
            computed_name = " ".join([p for p in name_parts if p]).strip() or "O'quvchi"
            db_user = User(
                id=user["id"],
                full_name=computed_name,
                username=user.get("username"),
                role=RoleEnum.student,
                language=LanguageEnum.uz,
            )
            session.add(db_user)
            await session.flush()

        student_name = db_user.full_name or user.get("first_name", "O'quvchi")
        student_username = db_user.username or user.get("username")

        # 2. Test natijasini saqlaymiz
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

        # Outcome turi
        outcome = "passed" if passed else ("beginner_recommended" if test.level.value == "A1" else "try_lower_level")

        # Xabarnomalarni asinxron fonda yuboramiz (o'quvchiga va o'qituvchiga/adminlarga)
        asyncio.create_task(
            _send_test_notifications(
                student_id=user["id"],
                student_name=student_name,
                student_username=student_username,
                test=test,
                score=correct_count,
                total=total,
                percent=percent,
                passed=passed,
            )
        )

        return {
            "score": correct_count,
            "total": total,
            "percent": round(percent, 1),
            "passed": passed,
            "outcome": outcome,
        }