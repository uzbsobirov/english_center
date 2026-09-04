"""
O'quvchi Web App API'si (TZ v2.6, 11-bo'lim).
- Progress (davomat foizi, test natijalari, badge'lar)
- Guruh dars jadvali
- Uy vazifalari
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func

from backend.database import async_session
from backend.models import (
    User, Enrollment, EnrollmentStatusEnum, Group, Course,
    Homework, TestResult, Attendance, AttendanceStatusEnum, UserBadge
)
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


@router.get("/schedule")
async def get_student_schedule(user: dict = Depends(get_current_telegram_user)):
    student_id = user["id"]
    from sqlalchemy.orm import aliased
    Teacher = aliased(User)
    async with async_session() as session:
        enr_res = await session.execute(
            select(Enrollment, Group, Course, Teacher)
            .join(Group, Enrollment.group_id == Group.id)
            .join(Course, Group.course_id == Course.id)
            .outerjoin(Teacher, Group.teacher_id == Teacher.id)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.is_active == True,
                Enrollment.status == EnrollmentStatusEnum.active,
            )
        )
        rows = enr_res.all()

        schedule_items = []
        for enr, grp, crs, teacher in rows:
            schedule_items.append({
                "group_id": grp.id,
                "group_name": grp.name,
                "course_title": crs.title.get("uz", "") if isinstance(crs.title, dict) else str(crs.title),
                "level": crs.level.value if hasattr(crs.level, "value") else str(crs.level),
                "schedule": grp.schedule,
                "room": grp.room,
                "zoom_link": grp.zoom_link,
                "group_chat_link": grp.group_chat_link,
                "teacher_name": teacher.full_name if teacher else "O'qituvchi",
            })
    return schedule_items


@router.get("/homework")
async def get_student_homework(user: dict = Depends(get_current_telegram_user)):
    student_id = user["id"]
    async with async_session() as session:
        enr_res = await session.execute(
            select(Enrollment.group_id)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.is_active == True,
                Enrollment.status == EnrollmentStatusEnum.active,
            )
        )
        group_ids = [r[0] for r in enr_res.all()]
        if not group_ids:
            return []

        hw_res = await session.execute(
            select(Homework, Group, User)
            .join(Group, Homework.group_id == Group.id)
            .outerjoin(User, Homework.teacher_id == User.id)
            .where(Homework.group_id.in_(group_ids))
            .order_by(Homework.created_at.desc())
        )
        hw_rows = hw_res.all()

        results = []
        for hw, grp, teacher in hw_rows:
            results.append({
                "id": hw.id,
                "group_id": grp.id,
                "group_name": grp.name,
                "title": hw.title,
                "description": hw.description,
                "file_id": hw.file_id,
                "due_at": hw.due_at.strftime("%d.%m.%Y %H:%M") if hw.due_at else None,
                "teacher_name": teacher.full_name if teacher else "O'qituvchi",
                "created_at": hw.created_at.strftime("%d.%m.%Y %H:%M") if hw.created_at else None,
            })
    return results

