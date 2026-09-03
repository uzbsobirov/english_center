"""
Test tizimi API'lari.
- GET /api/tests/active - joriy faol testni (savollar, to'g'ri javobsiz) qaytaradi
- POST /api/tests/{test_id}/submit - javoblarni qabul qiladi, ballni hisoblaydi, natijani saqlaydi
  va agar o'tgan bo'lsa, avtomatik ravishda free-dars so'rovini yaratib, o'qituvchilarga xabar beradi
"""
import re
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
    is_trial: bool = False


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
    Tanlangan daraja va yo'nalishga (IELTS/CEFR/General) mos eng so'nggi faol testni qaytaradi.
    """
    async with async_session() as session:
        query = select(Test).where(Test.is_active == True, Test.level == level)
        if type:
            query = query.where(Test.certificate_type.ilike(type))
        query = query.order_by(Test.created_at.desc())
        result = await session.execute(query.limit(1))
        test = result.scalar_one_or_none()

        # Agar tanlangan yo'nalishda topilmasa, shu darajadagi boshqa eng so'nggi faol testga fallback
        if test is None:
            result = await session.execute(
                select(Test).where(Test.is_active == True, Test.level == level).order_by(Test.created_at.desc()).limit(1)
            )
            test = result.scalar_one_or_none()

    if test is None:
        raise HTTPException(status_code=404, detail=f"{level} darajasi uchun faol test topilmadi")

    cooldown_info = None
    if test is not None:
        async with async_session() as session:
            from datetime import timedelta
            one_day_ago = datetime.utcnow() - timedelta(hours=24)
            recent_failed = await session.scalar(
                select(TestResult)
                .where(
                    TestResult.student_id == user["id"],
                    TestResult.test_id == test.id,
                    TestResult.passed == False,
                    TestResult.created_at >= one_day_ago,
                ).order_by(TestResult.created_at.desc()).limit(1)
            )
            if recent_failed:
                elapsed = (datetime.utcnow() - recent_failed.created_at).total_seconds()
                rem_hours = max(0.1, round((86400 - elapsed) / 3600, 1))
                level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
                lvl_str = test.level.value if hasattr(test.level, "value") else str(test.level)
                curr_idx = level_order.index(lvl_str) if lvl_str in level_order else 0
                lower_lvl = level_order[curr_idx - 1] if curr_idx > 0 else "A1"

                cooldown_info = {
                    "active": True,
                    "remaining_hours": rem_hours,
                    "lower_level": lower_lvl,
                }

    return _serialize_test(test, cooldown=cooldown_info)


def _serialize_test(test: Test, cooldown: dict | None = None) -> dict:
    safe_questions = []
    for idx, q in enumerate(test.questions or []):
        q_id = str(q.get("id") or f"q_{idx+1}")
        q_text = q.get("text") or q.get("question") or ""
        if isinstance(q_text, dict):
            q_text = q_text.get("uz", q_text.get("en", str(q_text)))
        safe_questions.append({
            "id": q_id,
            "type": q.get("type", "mcq"),
            "text": str(q_text),
            "options": q.get("options", []),
        })

    title_val = test.title
    if isinstance(title_val, dict):
        title_str = title_val.get("uz", title_val.get("en", "Test"))
    else:
        title_str = str(title_val)

    return {
        "id": test.id,
        "title": title_str,
        "level": test.level.value if hasattr(test.level, "value") else str(test.level),
        "certificate_type": test.certificate_type,
        "passing_score": float(test.passing_score),
        "questions": safe_questions,
        "cooldown": cooldown,
    }


from datetime import datetime
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from backend.services.user_service import get_admin_ids, get_teacher_ids
from backend.services.certificate_generator import generate_certificate_pdf
from backend.services.gamification import award_badge_if_eligible
from backend.models import (
    Test, TestResult, FreeTrialRequest, FreeTrialStatusEnum,
    User, RoleEnum, LanguageEnum, LevelEnum,
    Enrollment, EnrollmentStatusEnum, Group, Course
)


async def _send_test_notifications(
    student_id: int,
    student_name: str,
    student_username: str | None,
    student_phone: str | None,
    test: Test,
    score: int,
    total: int,
    percent: float,
    passed: bool,
    trial_id: int | None = None,
):
    """
    Test topshirilganda:
    1. O'quvchining o'ziga natijani yuboradi.
    2. Agar guruhda o'qisa, o'sha guruh o'qituvchisiga xabar beradi.
    3. Agar yangi o'quvchi (free trial) bo'lsa, o'qituvchilar va barcha adminlarga «Qabul qilish» tugmasi bilan xabar yuboradi.
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

    try:
        # 1. O'quvchining o'ziga botdan to'g'ridan-to'g'ri xabar
        student_msg = (
            f"📊 <b>Sizning test natijangiz:</b>\n\n"
            f"🎯 <b>Yo'nalish:</b> {cert_type} ({level_str})\n"
            f"📝 <b>Test:</b> {test_title_str}\n"
            f"📈 <b>To'plangan ball:</b> <b>{score}/{total}</b> (<b>{percent:.1f}%</b>)\n"
            f"📌 <b>Holat:</b> {status_icon}"
        )
        level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
        curr_idx = level_order.index(level_str) if level_str in level_order else 0
        lower_level = level_order[curr_idx - 1] if curr_idx > 0 else "A1"

        if not passed:
            if level_str != "A1":
                student_msg += (
                    f"\n\n💡 <b>Tavsiya:</b> Sizga mos guruhni topish uchun <b>{lower_level}</b> darajali testni topshirishingizni tavsiya qilamiz.\n"
                    f"⏳ <i>Xuddi shu ({level_str}) testni qayta topshirish uchun 24 soatdan so'ng ruxsat ochiladi.</i>"
                )
            else:
                student_msg += (
                    f"\n\n🌱 Siz ingliz tilini o'rganishni boshlang'ich <b>A1 (Beginner)</b> guruhidan boshlashingiz mumkin.\n"
                    f"Free darsga yozilish so'rovingiz qabul qilindi! ✅"
                )
        elif passed and trial_id:
            student_msg += "\n\n⏳ <b>So'rovingiz qabul qilindi!</b> Tez orada markaz o'qituvchisi siz bilan bog'lanib, bepul sinov darsi vaqti va manzilini ma'lum qiladi."

        try:
            await bot.send_message(student_id, student_msg)
        except Exception as e:
            print(f"⚠️ O'quvchiga xabar yuborishda xatolik ({student_id}): {e}")

        # Gamifikatsiya: starter badge
        try:
            await award_badge_if_eligible(student_id, "starter")
        except Exception:
            pass

        # 2. O'quvchi a'zo bo'lgan faol guruh bormi?
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

        student_link = f"<a href='tg://user?id={student_id}'>{student_name}</a>"
        student_user_str = f" (@{student_username})" if student_username else ""
        phone_str = student_phone or "Kiritilmagan"

        # 2. Agar bu Free Trial so'rovi bo'lsa (trial_id mavjud va testdan o'tgan)
        if trial_id and passed:
            admin_ids = await get_admin_ids()

            async with async_session() as session:
                teacher_res = await session.execute(
                    select(Group.teacher_id)
                    .join(Course, Group.course_id == Course.id)
                    .where(Course.level == test.level, Group.is_active == True)
                )
                level_teacher_ids = [int(t) for t in teacher_res.scalars().all() if t]

            recipients = set(admin_ids + level_teacher_ids)

            # «✅ Qabul qilish» va «❌ Rad etish» tugmalari bilan xabar
            accept_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"trial_accept:{trial_id}"),
                    InlineKeyboardButton(text="❌ Rad etish", callback_data=f"trial_reject:{trial_id}"),
                ]
            ])
            trial_msg = (
                f"🎯 <b>Yangi Free Dars So'rovi!</b>\n\n"
                f"👤 <b>O'quvchi:</b> {student_link}{student_user_str}\n"
                f"📱 <b>Telefon:</b> {phone_str}\n"
                f"🆔 <b>Telegram ID:</b> <code>{student_id}</code>\n"
                f"🎯 <b>Yo'nalish:</b> {cert_type} ({level_str})\n"
                f"📝 <b>Test:</b> {test_title_str}\n"
                f"📊 <b>Natija:</b> <b>{score}/{total}</b> (<b>{percent:.1f}%</b>) — ✅ O'tdi\n\n"
                f"<i>O'quvchini qabul qilish va bepul sinov darsiga taklif qilish uchun quyidagi tugmani bosing:</i>"
            )
            for recipient_id in recipients:
                try:
                    await bot.send_message(recipient_id, trial_msg, reply_markup=accept_keyboard)
                except Exception as e:
                    print(f"⚠️ Xabar yuborishda xatolik ({recipient_id}): {e}")

        # 3. Agar guruhda o'qiyotgan o'quvchi bo'lsa (va trial_id bo'lmasa)
        elif enrolled_groups:
            for enrollment, group in enrolled_groups:
                if group.teacher_id and group.teacher_id not in notified_teacher_ids:
                    notified_teacher_ids.add(group.teacher_id)
                    teacher_msg = (
                        f"📝 <b>Guruhingiz o'quvchisi test topshirdi!</b>\n\n"
                        f"👤 <b>O'quvchi:</b> {student_link}{student_user_str}\n"
                        f"👥 <b>Guruh:</b> <b>{group.name}</b>\n"
                        f"🎯 <b>Test:</b> {cert_type} — {level_str}\n"
                        f"📊 <b>Natija:</b> <b>{score}/{total}</b> (<b>{percent:.1f}%</b>)\n"
                        f"📌 <b>Holat:</b> {'✅ O\'tdi' if passed else '❌ O\'ta olmadi'}"
                    )
                    try:
                        await bot.send_message(group.teacher_id, teacher_msg)
                    except Exception as e:
                        print(f"⚠️ O'qituvchiga xabar yuborishda xatolik ({group.teacher_id}): {e}")

        # 4. Agar testdan o'ta olmagan bo'lsa -> faqat adminga axborot xabari
        elif not passed:
            admin_ids = await get_admin_ids()
            info_msg = (
                f"📊 <b>O'quvchi test topshirdi (O'ta olmadi):</b>\n\n"
                f"👤 <b>O'quvchi:</b> {student_link}{student_user_str} (ID: <code>{student_id}</code>)\n"
                f"📱 <b>Telefon:</b> {phone_str}\n"
                f"🎯 <b>Test:</b> {cert_type} ({level_str})\n"
                f"📈 <b>To'plagan bali:</b> <b>{score}/{total}</b> (<b>{percent:.1f}%</b>)\n"
                f"📌 <b>Holat:</b> ❌ O'tish balini to'play olmadi"
            )
            for admin_id in admin_ids:
                try:
                    await bot.send_message(int(admin_id), info_msg)
                except Exception:
                    pass

    finally:
        try:
            await bot.session.close()
        except Exception:
            pass


def _is_answer_correct(q: dict, student_ans: str | None) -> bool:
    if student_ans is None:
        return False

    correct = q.get("correct_answer")
    if correct is None:
        return False

    s_clean = str(student_ans).strip()
    c_clean = str(correct).strip()

    if not s_clean or not c_clean:
        return False

    # 1. To'g'ridan-to'g'ri tenglik (case-insensitive)
    if s_clean.lower() == c_clean.lower():
        return True

    q_type = q.get("type", "mcq")

    # 2. MCQ bo'lsa: "A) Variant" yoki "A" yoki "Variant"
    if q_type == "mcq":
        # Harf mosligi: "A" vs "A) Option"
        s_letter = s_clean[0].upper() if len(s_clean) > 0 and s_clean[0].isalpha() else ""
        c_letter = c_clean[0].upper() if len(c_clean) > 0 and c_clean[0].isalpha() else ""
        if s_letter and c_letter and s_letter == c_letter:
            return True
        # Matn mosligi: A) prefiksisiz
        s_no_prefix = re.sub(r"^[A-Ea-e][\)\.\:\-\s]+", "", s_clean).strip().lower()
        c_no_prefix = re.sub(r"^[A-Ea-e][\)\.\:\-\s]+", "", c_clean).strip().lower()
        if s_no_prefix and c_no_prefix and s_no_prefix == c_no_prefix:
            return True

    # 3. True / False bo'lsa
    elif q_type == "true_false":
        s_norm = "true" if s_clean.lower() in ("true", "t", "1", "to'g'ri") else ("false" if s_clean.lower() in ("false", "f", "0", "noto'g'ri") else s_clean.lower())
        c_norm = "true" if c_clean.lower() in ("true", "t", "1", "to'g'ri") else ("false" if c_clean.lower() in ("false", "f", "0", "noto'g'ri") else c_clean.lower())
        return s_norm == c_norm

    # 4. Fill blank yoki Short answer bo'lsa (bir nechta to'g'ri variantlar: "went / gone" yoki "London, England")
    elif q_type in ("fill_blank", "short_answer"):
        allowed = [a.strip().lower() for a in re.split(r"[/,;|]", c_clean) if a.strip()]
        if s_clean.lower() in allowed:
            return True
        # Punktuatsiyalarni olib tashlab solishtirish
        s_nopunct = re.sub(r"[^\w\s]", "", s_clean).strip().lower()
        for a in allowed:
            a_nopunct = re.sub(r"[^\w\s]", "", a).strip().lower()
            if s_nopunct == a_nopunct and s_nopunct:
                return True

    return False


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

        question_map = {}
        for idx, q in enumerate(test.questions or []):
            q_id = str(q.get("id") or f"q_{idx+1}")
            question_map[q_id] = q

        total = len(question_map)
        correct_count = 0
        answers_detail = []

        for item in payload.answers:
            q_obj = question_map.get(str(item.question_id), {})
            is_correct = _is_answer_correct(q_obj, item.answer)
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
        tg_first_name = user.get("first_name", "")
        tg_last_name = user.get("last_name", "")
        tg_full_name = " ".join([p for p in [tg_first_name, tg_last_name] if p]).strip()

        if not db_user:
            db_user = User(
                id=user["id"],
                full_name=tg_full_name or "O'quvchi",
                username=user.get("username"),
                role=RoleEnum.student,
                language=LanguageEnum.uz,
            )
            session.add(db_user)
            await session.flush()
        else:
            if tg_full_name and db_user.full_name in ("Bosh Admin", "Admin", "O'quvchi", "", "Dev Tester"):
                db_user.full_name = tg_full_name
            if user.get("username") and not db_user.username:
                db_user.username = user.get("username")

        student_name = db_user.full_name or tg_full_name or "O'quvchi"
        student_username = db_user.username or user.get("username")
        student_phone = db_user.phone

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
        await session.flush()

        # 3. FreeTrialRequest yaratish (FAQAT agar is_trial=True bo'lsa)
        trial_id = None
        if payload.is_trial and (passed or test.level == LevelEnum.A1):
            # Aynan shu kurs darajasiga tegishli faol enrollment bormi?
            has_matching_enrollment = await session.scalar(
                select(Enrollment.id)
                .join(Group, Enrollment.group_id == Group.id)
                .join(Course, Group.course_id == Course.id)
                .where(
                    Enrollment.student_id == user["id"],
                    Course.level == test.level,
                    Enrollment.is_active == True,
                    Enrollment.status == EnrollmentStatusEnum.active,
                ).limit(1)
            )
            if not has_matching_enrollment:
                # Yangi yoki mavjud pending trial
                existing_trial = await session.scalar(
                    select(FreeTrialRequest).where(
                        FreeTrialRequest.student_id == user["id"],
                        FreeTrialRequest.status == FreeTrialStatusEnum.pending,
                    ).limit(1)
                )
                if existing_trial:
                    existing_trial.test_result_id = test_result.id
                    trial_id = existing_trial.id
                else:
                    new_trial = FreeTrialRequest(
                        student_id=user["id"],
                        test_result_id=test_result.id,
                        status=FreeTrialStatusEnum.pending,
                    )
                    session.add(new_trial)
                    await session.flush()
                    trial_id = new_trial.id

        await session.commit()

        outcome = "passed" if passed else ("beginner_recommended" if test.level.value == "A1" else "try_lower_level")

        # Xabarnomalarni asinxron fonda yuboramiz (o'quvchiga, o'qituvchilarga va adminlarga)
        asyncio.create_task(
            _send_test_notifications(
                student_id=user["id"],
                student_name=student_name,
                student_username=student_username,
                student_phone=student_phone,
                test=test,
                score=correct_count,
                total=total,
                percent=percent,
                passed=passed,
                trial_id=trial_id,
            )
        )

        # Savollar bo'yicha batafsil tahlil (to'g'ri va xato javoblar)
        review_details = []
        for idx, q in enumerate(test.questions or []):
            q_id = str(q.get("id") or f"q_{idx+1}")
            q_text = q.get("text") or q.get("question") or ""
            if isinstance(q_text, dict):
                q_text = q_text.get("uz", q_text.get("en", str(q_text)))

            user_ans = None
            for item in payload.answers:
                if str(item.question_id) == q_id:
                    user_ans = item.answer
                    break

            corr_ans = q.get("correct_answer")
            is_correct = _is_answer_correct(q, user_ans)
            review_details.append({
                "id": q_id,
                "index": idx + 1,
                "type": q.get("type", "mcq"),
                "text": str(q_text),
                "options": q.get("options", []),
                "user_answer": user_ans,
                "correct_answer": corr_ans,
                "is_correct": is_correct,
            })

        return {
            "score": correct_count,
            "total": total,
            "percent": round(percent, 1),
            "passed": passed,
            "outcome": outcome,
            "review": review_details,
        }