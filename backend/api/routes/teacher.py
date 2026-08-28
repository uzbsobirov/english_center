"""
O'qituvchi Web App API'si (TZ v2.6, 7-bo'lim va 7.5.1).
- PDF yuklab AI orqali test generatsiya qilish (Self-check bilan)
- Testni faollashtirish va saqlash
- O'z guruhlari va o'quvchilar ro'yxati
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select

from backend.database import async_session
from backend.models import Test, Question, Group, Enrollment, User, RoleEnum, TestSourceEnum, LevelEnum
from backend.deps import get_current_telegram_user
from backend.services.ai_test_generator import extract_text_from_pdf, generate_test_from_pdf_text

router = APIRouter(prefix="/api/teacher", tags=["teacher"])


class CreateQuestionItem(BaseModel):
    order_num: int = 1
    type: str = "mcq"
    question: dict | str
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
    raw_text = extract_text_from_pdf(content)
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
    # Warningli savollar ko'rib chiqilganini tekshiramiz
    for q in payload.questions:
        if q.needs_review:
            raise HTTPException(
                status_code=400,
                detail="⚠️ Iltimos, barcha ogohlantirish belgisi bor savollarni ko'rib chiqing va tasdiqlang!",
            )

    async with async_session() as session:
        test = Test(
            teacher_id=user["id"],
            certificate_type=payload.certificate_type,
            level=LevelEnum(payload.level),
            title=payload.title,
            passing_score=payload.passing_score,
            time_limit_min=payload.time_limit_min,
            source=TestSourceEnum(payload.source),
            questions=[q.model_dump() for q in payload.questions],
            is_active=True,
        )
        session.add(test)
        await session.commit()
        test_id = test.id

    return {"status": "success", "test_id": test_id, "message": "Test muvaffaqiyatli faollashtirildi!"}
