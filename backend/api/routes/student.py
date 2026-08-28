"""
O'quvchi Web App API'si (TZ v2.6, 11-bo'lim).
- Progress (davomat foizi, test natijalari, badge'lar)
- Guruh dars jadvali
- Uy vazifalari
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func

from backend.database import async_session
from backend.models import User, Enrollment, Group, Course, Homework, TestResult, Attendance, AttendanceStatusEnum, UserBadge
from backend.deps import get_current_telegram_user

router = APIRouter(prefix="/api/student", tags=["student"])


@router.get("/progress")
async def get_student_progress(user: dict = Depends(get_current_telegram_user)):
    student_id = user["id"]

    async with async_session() as session:
        # Davomat foizi
        total_att_res = await session.execute(
            select(func.count(Attendance.id)).where(Attendance.student_id == student_id)
        )
        total_att = total_att_res.scalar() or 0

        present_att_res = await session.execute(
            select(func.count(Attendance.id)).where(
                Attendance.student_id == student_id,
                Attendance.status.in_([AttendanceStatusEnum.present, AttendanceStatusEnum.late]),
            )
        )
        present_att = present_att_res.scalar() or 0
        attendance_percent = (present_att / total_att * 100) if total_att > 0 else 100.0

        # Test natijalari
        tests_res = await session.execute(
            select(TestResult).where(TestResult.student_id == student_id).order_by(TestResult.created_at.desc())
        )
        test_results = tests_res.scalars().all()
        avg_score = sum(float(t.percent) for t in test_results) / len(test_results) if test_results else 0.0

        # Badge'lar
        badges_res = await session.execute(
            select(UserBadge).where(UserBadge.user_id == student_id)
        )
        badges = [b.badge_type for b in badges_res.scalars().all()]

    return {
        "attendance_percent": round(attendance_percent, 1),
        "total_lessons_tracked": total_att,
        "average_test_score": round(avg_score, 1),
        "tests_taken": len(test_results),
        "badges": badges,
    }
