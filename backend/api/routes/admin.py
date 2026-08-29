"""
Admin Web App API'si (TZ v2.6, 8-bo'lim).
- Dashboard statistikasi
- Kurslar va guruhlar boshqaruvi
- O'quvchilar ro'yxati
- Barcha to'lovlar va tasdiqlash
- Pro Broadcast yuborish
"""
import asyncio
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, update

from backend.database import async_session
from backend.models import (
    Payment, PaymentStatusEnum, PaymentMethodEnum, User, RoleEnum,
    Group, Course, Enrollment, EnrollmentStatusEnum, FreeTrialRequest, ReferralBonus,
)
from backend.deps import get_current_telegram_user
from backend.services.user_service import is_admin_or_manager
from backend.services.gamification import award_badge_if_eligible

router = APIRouter(prefix="/api/admin", tags=["admin"])


class BroadcastPayload(BaseModel):
    text: str
    target_role: str | None = "all"  # student / teacher / all
    level: str | None = None


class CoursePayload(BaseModel):
    title_uz: str
    title_ru: str | None = None
    title_en: str | None = None
    type: str = "General"  # IELTS, CEFR, General
    level: str = "A1"
    price: float
    price_per_lesson: float | None = None
    duration_months: int = 1
    lessons_per_week: int = 3
    description_uz: str | None = ""
    description_ru: str | None = ""
    description_en: str | None = ""


class GroupPayload(BaseModel):
    course_id: int
    name: str
    teacher_id: int | None = None
    schedule_days: list[str] = ["Monday", "Wednesday", "Friday"]
    schedule_time: str = "18:00"
    room: str | None = "Asosiy xona"
    max_students: int = 12
    zoom_link: str | None = None


@router.get("/dashboard")
async def get_admin_dashboard(user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        total_students_res = await session.execute(
            select(func.count(User.id)).where(User.role == RoleEnum.student)
        )
        total_students = total_students_res.scalar() or 0

        active_groups_res = await session.execute(
            select(func.count(Group.id)).where(Group.is_active == True)
        )
        active_groups = active_groups_res.scalar() or 0

        payments_sum_res = await session.execute(
            select(func.sum(Payment.amount)).where(Payment.status == PaymentStatusEnum.confirmed)
        )
        total_revenue = float(payments_sum_res.scalar() or 0)

        pending_payments_res = await session.execute(
            select(func.count(Payment.id)).where(Payment.status == PaymentStatusEnum.pending)
        )
        pending_payments = pending_payments_res.scalar() or 0

        pending_trials_res = await session.execute(
            select(func.count(FreeTrialRequest.id)).where(FreeTrialRequest.status == "pending")
        )
        pending_trials = pending_trials_res.scalar() or 0

        total_teachers_res = await session.execute(
            select(func.count(User.id)).where(User.role == RoleEnum.teacher)
        )
        total_teachers = total_teachers_res.scalar() or 0

    return {
        "total_students": total_students,
        "active_groups": active_groups,
        "total_revenue": total_revenue,
        "pending_payments": pending_payments,
        "pending_trials": pending_trials,
        "total_teachers": total_teachers,
    }


@router.get("/groups")
async def get_admin_groups(user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        groups_res = await session.execute(
            select(Group, Course)
            .join(Course, Group.course_id == Course.id)
            .order_by(Group.id.desc())
        )
        group_rows = groups_res.all()

        results = []
        for group, course in group_rows:
            teacher = await session.get(User, group.teacher_id) if group.teacher_id else None
            student_count_res = await session.execute(
                select(func.count(Enrollment.id)).where(
                    Enrollment.group_id == group.id,
                    Enrollment.is_active == True,
                )
            )
            student_count = student_count_res.scalar() or 0

            results.append({
                "id": group.id,
                "name": group.name,
                "course_id": course.id,
                "course_title": course.title.get("uz", "") if isinstance(course.title, dict) else str(course.title),
                "level": course.level.value if hasattr(course.level, "value") else str(course.level),
                "price": float(course.price),
                "teacher_id": teacher.id if teacher else None,
                "teacher_name": teacher.full_name if teacher else "Tayinlanmagan",
                "schedule": group.schedule,
                "room": group.room,
                "max_students": group.max_students,
                "enrolled_students": student_count,
                "is_active": group.is_active,
            })

    return results


@router.get("/courses")
async def get_admin_courses(user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        courses_res = await session.execute(
            select(Course).order_by(Course.id.desc())
        )
        courses = courses_res.scalars().all()

        results = []
        for c in courses:
            groups_count_res = await session.execute(
                select(func.count(Group.id)).where(Group.course_id == c.id, Group.is_active == True)
            )
            groups_count = groups_count_res.scalar() or 0

            title_dict = c.title if isinstance(c.title, dict) else {"uz": str(c.title)}
            desc_dict = c.description if isinstance(c.description, dict) else {"uz": str(c.description or "")}

            results.append({
                "id": c.id,
                "title": title_dict,
                "title_uz": title_dict.get("uz", ""),
                "title_ru": title_dict.get("ru", ""),
                "title_en": title_dict.get("en", ""),
                "type": c.type.value if hasattr(c.type, "value") else str(c.type),
                "level": c.level.value if hasattr(c.level, "value") else str(c.level),
                "price": float(c.price),
                "price_per_lesson": float(c.price_per_lesson) if c.price_per_lesson else c.effective_price_per_lesson,
                "duration_months": c.duration_months,
                "lessons_per_week": c.lessons_per_week,
                "description": desc_dict,
                "description_uz": desc_dict.get("uz", ""),
                "description_ru": desc_dict.get("ru", ""),
                "description_en": desc_dict.get("en", ""),
                "groups_count": groups_count,
                "is_active": c.is_active,
            })

    return results


@router.post("/courses")
async def create_admin_course(payload: CoursePayload, user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    title_dict = {
        "uz": payload.title_uz,
        "ru": payload.title_ru or payload.title_uz,
        "en": payload.title_en or payload.title_uz,
    }
    desc_dict = {
        "uz": payload.description_uz or "",
        "ru": payload.description_ru or payload.description_uz or "",
        "en": payload.description_en or payload.description_uz or "",
    }

    async with async_session() as session:
        course = Course(
            title=title_dict,
            type=payload.type,
            level=payload.level,
            description=desc_dict,
            duration_months=payload.duration_months,
            lessons_per_week=payload.lessons_per_week,
            price=payload.price,
            price_per_lesson=payload.price_per_lesson,
            is_active=True,
        )
        session.add(course)
        await session.commit()
        await session.refresh(course)

    return {"status": "success", "course_id": course.id, "message": "Kurs muvaffaqiyatli yaratildi!"}


@router.put("/courses/{course_id}")
async def update_admin_course(course_id: int, payload: CoursePayload, user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    title_dict = {
        "uz": payload.title_uz,
        "ru": payload.title_ru or payload.title_uz,
        "en": payload.title_en or payload.title_uz,
    }
    desc_dict = {
        "uz": payload.description_uz or "",
        "ru": payload.description_ru or payload.description_uz or "",
        "en": payload.description_en or payload.description_uz or "",
    }

    async with async_session() as session:
        course = await session.get(Course, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Kurs topilmadi.")

        course.title = title_dict
        course.type = payload.type
        course.level = payload.level
        course.description = desc_dict
        course.duration_months = payload.duration_months
        course.lessons_per_week = payload.lessons_per_week
        course.price = payload.price
        course.price_per_lesson = payload.price_per_lesson

        await session.commit()

    return {"status": "success", "message": "Kurs yangilandi!"}


@router.delete("/courses/{course_id}")
async def toggle_admin_course(course_id: int, user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        course = await session.get(Course, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Kurs topilmadi.")

        course.is_active = not course.is_active
        await session.commit()

    return {"status": "success", "is_active": course.is_active, "message": "Kurs holati o'zgartirildi!"}


@router.get("/teachers")
async def get_admin_teachers(user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        teachers_res = await session.execute(
            select(User).where(User.role.in_([RoleEnum.teacher, RoleEnum.admin]), User.is_active == True)
        )
        teachers = teachers_res.scalars().all()

        return [
            {
                "id": t.id,
                "full_name": t.full_name,
                "username": t.username,
                "role": t.role.value if hasattr(t.role, "value") else str(t.role),
            }
            for t in teachers
        ]


@router.post("/groups")
async def create_admin_group(payload: GroupPayload, user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    schedule_list = [{"day": d, "time": payload.schedule_time} for d in payload.schedule_days]

    async with async_session() as session:
        group = Group(
            course_id=payload.course_id,
            name=payload.name,
            teacher_id=payload.teacher_id,
            schedule=schedule_list,
            room=payload.room,
            max_students=payload.max_students,
            zoom_link=payload.zoom_link,
            is_active=True,
        )
        session.add(group)
        await session.commit()
        await session.refresh(group)

    return {"status": "success", "group_id": group.id, "message": "Guruh muvaffaqiyatli yaratildi!"}


@router.put("/groups/{group_id}")
async def update_admin_group(group_id: int, payload: GroupPayload, user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    schedule_list = [{"day": d, "time": payload.schedule_time} for d in payload.schedule_days]

    async with async_session() as session:
        group = await session.get(Group, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Guruh topilmadi.")

        group.course_id = payload.course_id
        group.name = payload.name
        group.teacher_id = payload.teacher_id
        group.schedule = schedule_list
        group.room = payload.room
        group.max_students = payload.max_students
        group.zoom_link = payload.zoom_link

        await session.commit()

    return {"status": "success", "message": "Guruh yangilandi!"}


@router.delete("/groups/{group_id}")
async def toggle_admin_group(group_id: int, user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        group = await session.get(Group, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Guruh topilmadi.")

        group.is_active = not group.is_active
        await session.commit()

    return {"status": "success", "is_active": group.is_active, "message": "Guruh holati o'zgartirildi!"}


@router.get("/students")
async def get_admin_students(user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        students_res = await session.execute(
            select(User).where(User.role == RoleEnum.student).order_by(User.created_at.desc())
        )
        students = students_res.scalars().all()

        results = []
        for s in students:
            # Active group
            enr_res = await session.execute(
                select(Enrollment, Group)
                .join(Group, Enrollment.group_id == Group.id)
                .where(Enrollment.student_id == s.id, Enrollment.is_active == True)
            )
            enr_row = enr_res.first()
            group_name = enr_row[1].name if enr_row else "Guruhsiz"

            results.append({
                "id": s.id,
                "full_name": s.full_name,
                "username": s.username,
                "phone": s.phone,
                "language": s.language.value if hasattr(s.language, "value") else str(s.language),
                "group_name": group_name,
                "created_at": s.created_at.strftime("%d.%m.%Y") if s.created_at else "-",
            })

    return results


@router.get("/payments")
async def get_admin_payments(user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        payments_res = await session.execute(
            select(Payment, User, Group)
            .join(User, Payment.student_id == User.id)
            .join(Group, Payment.group_id == Group.id)
            .order_by(Payment.created_at.desc())
        )
        rows = payments_res.all()

        results = []
        for p, student, group in rows:
            results.append({
                "id": p.id,
                "student_id": student.id,
                "student_name": student.full_name,
                "student_username": student.username,
                "group_id": group.id,
                "group_name": group.name,
                "amount": float(p.amount),
                "discount_amount": float(p.discount_amount or 0.0),
                "method": p.method.value if hasattr(p.method, "value") else str(p.method),
                "status": p.status.value if hasattr(p.status, "value") else str(p.status),
                "created_at": p.created_at.strftime("%d.%m.%Y %H:%M") if p.created_at else "-",
                "paid_at": p.paid_at.strftime("%d.%m.%Y %H:%M") if p.paid_at else None,
            })

    return results


async def _send_approve_notifications(student_id: int, student_name: str, group_name: str, teacher_name: str, schedule_str: str, room_str: str, referrer_id: int | None):
    from main import bot
    congrats_text = (
        f"🎉 <b>To'lovingiz tasdiqlandi!</b>\n\n"
        f"Siz rasman guruhga qabul qilindingiz:\n"
        f"👥 <b>Guruh:</b> {group_name}\n"
        f"👨‍🏫 <b>O'qituvchi:</b> {teacher_name}\n"
        f"🗓 <b>Dars jadvali:</b> {schedule_str}\n"
        f"🚪 <b>Xona / Manzil:</b> {room_str}\n\n"
        f"Endi bot menyusidan «📅 Jadvalim» va «📋 Uy Vazifam» bo'limlarini kuzatib borishingiz mumkin. Muvaffaqiyat tilaymiz! 🚀"
    )
    try:
        await bot.send_message(student_id, congrats_text, parse_mode="HTML")
    except Exception:
        pass

    if referrer_id:
        try:
            await award_badge_if_eligible(referrer_id, "ambassador")
            await bot.send_message(
                referrer_id,
                f"🎁 <b>Ajoyib xabar!</b>\n\n"
                f"Siz taklif qilgan do'stingiz ({student_name}) kurs to'lovini amalga oshirdi va o'qishni boshladi!\n"
                f"Sizga keyingi oy to'lovi uchun <b>+5% chegirma bonusi</b> va 👥 <b>Ambassador badge</b> berildi! 🌟",
            )
        except Exception:
            pass


@router.post("/payments/{payment_id}/approve")
async def approve_admin_payment(payment_id: int, user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        result = await session.execute(
            update(Payment)
            .where(Payment.id == payment_id, Payment.status == PaymentStatusEnum.pending)
            .values(
                status=PaymentStatusEnum.confirmed,
                confirmed_by=user["id"],
                paid_at=datetime.utcnow(),
            )
        )
        await session.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=400, detail="Bu to'lov allaqachon ko'rib chiqilgan yoki topilmadi.")

        payment = await session.get(Payment, payment_id)
        group = await session.get(Group, payment.group_id)
        teacher = await session.get(User, group.teacher_id) if group and group.teacher_id else None

        # Enrollment yaratish
        existing = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == payment.student_id,
                Enrollment.group_id == payment.group_id,
            )
        )
        if existing.scalar_one_or_none() is None:
            session.add(Enrollment(
                student_id=payment.student_id,
                group_id=payment.group_id,
                status=EnrollmentStatusEnum.active,
                enrolled_at=datetime.utcnow(),
            ))

        # Referrer bonus (faqat to'liq to'lov bo'lganda)
        student = await session.get(User, payment.student_id)
        course = await session.get(Course, group.course_id) if group else None
        course_price = float(course.price) if course else 0.0
        is_full_payment = (float(payment.amount) + float(payment.discount_amount or 0.0)) >= course_price

        referrer_id = None
        if is_full_payment and student and student.referred_by and not student.referral_bonus_given:
            session.add(ReferralBonus(
                user_id=student.referred_by,
                referred_student_id=student.id,
                bonus_percent=5.0,
                status="pending",
                is_used=False,
            ))
            student.referral_bonus_given = True
            referrer_id = student.referred_by

        await session.commit()

    from backend.utils.formatters import format_schedule
    teacher_name = teacher.full_name if teacher else "O'qituvchi"
    schedule_str = format_schedule(group.schedule if group else None, student.language.value if student and student.language else "uz")

    asyncio.create_task(_send_approve_notifications(
        student_id=payment.student_id,
        student_name=student.full_name,
        group_name=group.name if group else "",
        teacher_name=teacher_name,
        schedule_str=schedule_str,
        room_str=group.room or "O'quv markazi",
        referrer_id=referrer_id,
    ))

    return {"status": "success", "message": "To'lov tasdiqlandi va o'quvchi guruhga a'zo qilindi."}



@router.post("/payments/{payment_id}/reject")
async def reject_admin_payment(payment_id: int, user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        result = await session.execute(
            update(Payment)
            .where(Payment.id == payment_id, Payment.status == PaymentStatusEnum.pending)
            .values(status=PaymentStatusEnum.rejected)
        )
        await session.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=400, detail="Bu to'lov allaqachon ko'rib chiqilgan yoki topilmadi.")

        payment = await session.get(Payment, payment_id)

    from main import bot
    try:
        await bot.send_message(
            payment.student_id,
            "❌ Afsuski, to'lov so'rovingiz rad etildi. Iltimos, ma'muriyat bilan bog'laning.",
        )
    except Exception:
        pass

    return {"status": "success", "message": "To'lov rad etildi."}


async def _send_broadcast_worker(user_ids: list[int], text: str):
    from main import bot
    for uid in user_ids:
        try:
            await bot.send_message(uid, text, parse_mode="HTML")
            await asyncio.sleep(0.05)  # Telegram rate limit prevention
        except Exception:
            continue


@router.post("/broadcast")
async def broadcast_message(
    payload: BroadcastPayload,
    user: dict = Depends(get_current_telegram_user),
):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        query = select(User.id).where(User.is_active == True)
        if payload.target_role and payload.target_role != "all":
            query = query.where(User.role == RoleEnum(payload.target_role))
        if payload.level:
            query = query.where(User.level == payload.level)

        res = await session.execute(query)
        user_ids = res.scalars().all()

    asyncio.create_task(_send_broadcast_worker(list(user_ids), payload.text))

    return {
        "status": "success",
        "sent_count": len(user_ids),
        "total_target": len(user_ids),
        "message": f"Xabar {len(user_ids)} ta foydalanuvchiga yuborilmoqda.",
    }

