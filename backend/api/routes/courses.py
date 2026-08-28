"""
Kurslar va Guruhlar API'si.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from pydantic import BaseModel
from backend.database import async_session
from backend.models import Course, Group, Enrollment, User, LevelEnum, CourseTypeEnum
from backend.deps import get_current_telegram_user
from backend.services.user_service import is_admin_or_manager

router = APIRouter(prefix="/api/courses", tags=["courses"])


class CourseCreatePayload(BaseModel):
    title: dict  # {"uz": "...", "ru": "...", "en": "..."}
    type: str = "General"  # IELTS, CEFR, General
    level: str = "A1"  # A1, A2, B1, B2, C1, C2
    description: dict | None = None
    duration_months: int = 3
    lessons_per_week: int = 3
    price: float = 1200000.0


class GroupCreatePayload(BaseModel):
    teacher_id: int
    name: str
    schedule: list = []  # [{"day": "Monday", "time": "18:00"}]
    room: str | None = None
    max_students: int = 12
    group_chat_link: str | None = None
    zoom_link: str | None = None


@router.get("")
async def get_courses():
    async with async_session() as session:
        res = await session.execute(select(Course).where(Course.is_active == True))
        courses = res.scalars().all()
        return [
            {
                "id": c.id,
                "title": c.title,
                "type": c.type.value if hasattr(c.type, "value") else c.type,
                "level": c.level.value,
                "description": c.description,
                "duration_months": c.duration_months,
                "lessons_per_week": c.lessons_per_week,
                "price": float(c.price),
                "image_file_id": c.image_file_id,
            }
            for c in courses
        ]


@router.post("")
async def create_course(
    payload: CourseCreatePayload,
    user: dict = Depends(get_current_telegram_user),
):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        course = Course(
            title=payload.title,
            type=CourseTypeEnum(payload.type),
            level=LevelEnum(payload.level),
            description=payload.description or {},
            duration_months=payload.duration_months,
            lessons_per_week=payload.lessons_per_week,
            price=payload.price,
            is_active=True,
        )
        session.add(course)
        await session.commit()
        await session.refresh(course)
        return {"status": "success", "course_id": course.id}


@router.get("/{course_id}/groups")
async def get_course_groups(course_id: int):
    async with async_session() as session:
        res = await session.execute(
            select(Group).where(Group.course_id == course_id, Group.is_active == True)
        )
        groups = res.scalars().all()
        return [
            {
                "id": g.id,
                "name": g.name,
                "schedule": g.schedule,
                "room": g.room,
                "max_students": g.max_students,
                "group_chat_link": g.group_chat_link,
                "zoom_link": g.zoom_link,
            }
            for g in groups
        ]


@router.post("/{course_id}/groups")
async def create_group(
    course_id: int,
    payload: GroupCreatePayload,
    user: dict = Depends(get_current_telegram_user),
):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        course = await session.get(Course, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Kurs topilmadi.")

        group = Group(
            course_id=course_id,
            teacher_id=payload.teacher_id,
            name=payload.name,
            schedule=payload.schedule,
            room=payload.room,
            max_students=payload.max_students,
            group_chat_link=payload.group_chat_link,
            zoom_link=payload.zoom_link,
            is_active=True,
        )
        session.add(group)
        await session.commit()
        await session.refresh(group)
        return {"status": "success", "group_id": group.id}
