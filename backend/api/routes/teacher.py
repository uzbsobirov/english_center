"""
O'qituvchi Web App API'si (TZ v2.6, 7-bo'lim va 7.5.1).
- PDF yuklab AI orqali test generatsiya qilish (Self-check bilan)
- Testni faollashtirish va saqlash
- Mavjud testlar ro'yxatini olish va tahrirlash (Edit / Update)
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select, func

from backend.database import async_session
from backend.models import Test, Question, Group, Enrollment, User, RoleEnum, TestSourceEnum, LevelEnum, Course
from backend.deps import get_current_telegram_user
from backend.services.ai_test_generator import extract_text_from_pdf, generate_test_from_pdf_text
from backend.services.user_service import is_admin_or_manager, is_teacher

router = APIRouter(prefix="/api/teacher", tags=["teacher"])


@router.get("/user-roles")
async def get_user_roles(user: dict = Depends(get_current_telegram_user)):
    user_id = user["id"]
    is_adm = await is_admin_or_manager(user_id)
    is_t = await is_teacher(user_id)
    return {
        "user_id": user_id,
        "name": user.get("full_name") or user.get("first_name", "Foydalanuvchi"),
        "is_admin": is_adm,
        "is_teacher": is_t,
        "is_dual_role": (is_adm and is_t),
    }


@router.get("/workspace")
async def get_teacher_workspace(user: dict = Depends(get_current_telegram_user)):
    user_id = user["id"]
    is_adm = await is_admin_or_manager(user_id)
    is_t = await is_teacher(user_id)

    if not is_adm and not is_t:
        raise HTTPException(status_code=403, detail="Faqat o'qituvchilar va adminlar uchun.")

    async with async_session() as session:
        # Guruhlarni aniqlaymiz
        grp_query = select(Group, Course).join(Course, Group.course_id == Course.id).where(Group.is_active == True)
        
        # Agar admin bo'lsa va o'zining shaxsiy guruhlari bo'lsa, o'z guruhlari ko'rinadi; aks holda barcha guruhlar
        own_check = await session.execute(select(Group.id).where(Group.teacher_id == user_id, Group.is_active == True).limit(1))
        if own_check.scalar_one_or_none():
            grp_query = grp_query.where(Group.teacher_id == user_id)
        elif not is_adm:
            grp_query = grp_query.where(Group.teacher_id == user_id)

        grp_rows = (await session.execute(grp_query.order_by(Group.id.desc()))).all()

        my_groups = []
        all_student_ids = set()

        for grp, crs in grp_rows:
            enr_res = await session.execute(
                select(Enrollment, User)
                .join(User, Enrollment.student_id == User.id)
                .where(Enrollment.group_id == grp.id, Enrollment.is_active == True)
            )
            enr_rows = enr_res.all()
            students_list = []
            for enr, u in enr_rows:
                all_student_ids.add(u.id)
                students_list.append({
                    "id": u.id,
                    "full_name": u.full_name or "Noma'lum",
                    "username": u.username,
                    "phone": u.phone or "—",
                    "enrolled_at": enr.enrolled_at.strftime("%d.%m.%Y") if enr.enrolled_at else "-",
                })

            title_str = crs.title.get("uz", "") if isinstance(crs.title, dict) else str(crs.title)
            my_groups.append({
                "id": grp.id,
                "name": grp.name,
                "course_id": crs.id,
                "course_name": title_str,
                "level": crs.level.value if hasattr(crs.level, "value") else str(crs.level),
                "schedule": grp.schedule,
                "room": grp.room,
                "group_chat_link": grp.group_chat_link,
                "zoom_link": grp.zoom_link,
                "max_students": grp.max_students,
                "enrolled_count": len(students_list),
                "students": students_list,
            })

        tests_count_res = await session.execute(select(func.count(Test.id)).where(Test.is_active == True))
        tests_count = tests_count_res.scalar() or 0

        return {
            "teacher_id": user_id,
            "teacher_name": user.get("full_name") or user.get("first_name", "Ustoz"),
            "academic_stats": {
                "total_groups": len(my_groups),
                "total_students": len(all_student_ids),
                "active_tests": tests_count,
            },
            "groups": my_groups,
        }


class CreateQuestionItem(BaseModel):
    id: str | None = None
    order_num: int = 1
    type: str = "mcq"
    question: dict | str | None = None
    text: str | None = None
    options: list[str] | None = None
    correct_answer: str
    points: int = 1
    ai_generated: bool = False
    needs_review: bool = False


class SaveTestPayload(BaseModel):
    certificate_type: str = "IELTS"
    level: str = "B1"
    title: dict = {"uz": "IELTS B1 Test", "ru": "Тест IELTS B1", "en": "IELTS B1 Test"}
    passing_score: float = 70.0
    time_limit_min: int = 20
    source: str = "manual"
    questions: list[CreateQuestionItem]


@router.get("/tests")
async def get_teacher_tests(user: dict = Depends(get_current_telegram_user)):
    """Mavjud barcha testlar ro'yxatini qaytaradi."""
    async with async_session() as session:
        result = await session.execute(
            select(Test).order_by(Test.created_at.desc())
        )
        tests = result.scalars().all()

    return [
        {
            "id": t.id,
            "certificate_type": t.certificate_type,
            "level": t.level.value if hasattr(t.level, "value") else str(t.level),
            "title": t.title,
            "title_uz": t.title.get("uz", "Test") if isinstance(t.title, dict) else str(t.title),
            "passing_score": float(t.passing_score),
            "time_limit_min": t.time_limit_min,
            "source": t.source.value if hasattr(t.source, "value") else str(t.source),
            "total_questions": len(t.questions or []),
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tests
    ]


@router.get("/tests/{test_id}")
async def get_test_detail(test_id: int, user: dict = Depends(get_current_telegram_user)):
    """Bitta testning to'liq savollari va parametrlarini qaytaradi."""
    async with async_session() as session:
        test = await session.get(Test, test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test topilmadi")

    # Savollarni standartlashtiramiz
    formatted_questions = []
    for idx, q in enumerate(test.questions or []):
        q_text = q.get("text") or q.get("question") or ""
        if isinstance(q_text, dict):
            q_text = q_text.get("uz", q_text.get("en", ""))
        formatted_questions.append({
            "id": q.get("id") or f"q_{idx+1}",
            "order_num": q.get("order_num", idx + 1),
            "type": q.get("type", "mcq"),
            "text": str(q_text),
            "options": q.get("options", []),
            "correct_answer": q.get("correct_answer", ""),
            "points": q.get("points", 1),
            "ai_generated": q.get("ai_generated", False),
            "needs_review": q.get("needs_review", False),
        })

    return {
        "id": test.id,
        "certificate_type": test.certificate_type,
        "level": test.level.value if hasattr(test.level, "value") else str(test.level),
        "title": test.title,
        "title_uz": test.title.get("uz", "Test") if isinstance(test.title, dict) else str(test.title),
        "passing_score": float(test.passing_score),
        "time_limit_min": test.time_limit_min,
        "source": test.source.value if hasattr(test.source, "value") else str(test.source),
        "questions": formatted_questions,
        "is_active": test.is_active,
    }


@router.post("/generate-test-from-pdf")
async def generate_test_from_pdf(
    file: UploadFile = File(...),
    certificate_type: str = Form("IELTS"),
    level: str = Form("B1"),
    user: dict = Depends(get_current_telegram_user),
):
    """
    TZ 7.5.1: PDF fayldan test generatsiya qilish.
    Self-check bilan ⚠️ warning belgili savollar ajratiladi.
    """
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Yuklangan PDF fayli bo'sh.")

    raw_text = extract_text_from_pdf(content)
    if not raw_text or len(raw_text.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="PDF faylidan matn ajratib bo'lmadi. Iltimos, PDF faylida matn mavjudligini tekshiring (skaner qilingan rasmli PDF bo'lmasligi kerak).",
        )

    questions = await generate_test_from_pdf_text(raw_text, cert_type=certificate_type, level=level)

    return {
        "certificate_type": certificate_type,
        "level": level,
        "source": "ai_pdf",
        "total_questions": len(questions),
        "warning_count": sum(1 for q in questions if q.get("needs_review")),
        "questions": questions,
    }


@router.post("/save-test")
async def save_test(
    payload: SaveTestPayload,
    user: dict = Depends(get_current_telegram_user),
):
    """
    O'qituvchi tomonidan tekshirilgan va tasdiqlangan testni bazaga saqlash (TZ 7.5 va 7.5.1).
    """
    for q in payload.questions:
        if q.needs_review:
            raise HTTPException(
                status_code=400,
                detail="⚠️ Iltimos, barcha ogohlantirish belgisi bor savollarni ko'rib chiqing va tasdiqlang!",
            )

    def _format_q(q, idx):
        text_val = q.text or q.question or ""
        return {
            "id": q.id or f"q_{idx+1}",
            "order_num": idx + 1,
            "type": q.type,
            "text": text_val,
            "question": text_val,
            "options": q.options,
            "correct_answer": q.correct_answer,
            "points": q.points,
            "ai_generated": q.ai_generated,
            "needs_review": False,
        }

    async with async_session() as session:
        t_user = await session.get(User, user["id"])
        teacher_fk = t_user.id if t_user else None

        test = Test(
            teacher_id=teacher_fk,
            certificate_type=payload.certificate_type,
            level=LevelEnum(payload.level),
            title=payload.title,
            passing_score=payload.passing_score,
            time_limit_min=payload.time_limit_min,
            source=TestSourceEnum(payload.source),
            questions=[_format_q(q, idx) for idx, q in enumerate(payload.questions)],
            is_active=True,
        )
        session.add(test)
        await session.commit()
        test_id = test.id

    return {
        "status": "success",
        "test_id": test_id,
        "message": f"🎉 {payload.certificate_type} {payload.level} testi muvaffaqiyatli saqlandi va faollashtirildi! O'quvchilar ishlashiga tayyor.",
    }


@router.put("/tests/{test_id}")
async def update_test(
    test_id: int,
    payload: SaveTestPayload,
    user: dict = Depends(get_current_telegram_user),
):
    """Mavjud testni tahrirlash va yangilash."""
    async with async_session() as session:
        test = await session.get(Test, test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test topilmadi")

        def _format_q(q, idx):
            text_val = q.text or q.question or ""
            return {
                "id": q.id or f"q_{idx+1}",
                "order_num": idx + 1,
                "type": q.type,
                "text": text_val,
                "question": text_val,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "points": q.points,
                "ai_generated": q.ai_generated,
                "needs_review": False,
            }

        test.certificate_type = payload.certificate_type
        test.level = LevelEnum(payload.level)
        test.title = payload.title
        test.passing_score = payload.passing_score
        test.time_limit_min = payload.time_limit_min
        test.questions = [_format_q(q, idx) for idx, q in enumerate(payload.questions)]

        await session.commit()

    return {
        "status": "success",
        "test_id": test_id,
        "message": f"✅ {payload.certificate_type} {payload.level} testi muvaffaqiyatli yangilandi!",
    }
