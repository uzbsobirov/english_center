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
    CenterSetting, Refund,
)
from backend.deps import get_current_telegram_user
from backend.services.user_service import is_admin_or_manager, add_admin, remove_admin
from backend.services.gamification import award_badge_if_eligible

router = APIRouter(prefix="/api/admin", tags=["admin"])


class BroadcastPayload(BaseModel):
    text: str
    target_role: str | None = "all"  # student / teacher / IELTS / CEFR / all
    level: str | None = None
    button_text: str | None = None
    button_url: str | None = None


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
    group_chat_link: str | None = None
    zoom_link: str | None = None


@router.get("/dashboard")
async def get_admin_dashboard(user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        total_students_res = await session.execute(
            select(func.count(User.id.distinct())).where(User.role == RoleEnum.student)
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
                select(func.count(Enrollment.id.distinct()))
                .where(
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
                "group_chat_link": group.group_chat_link,
                "zoom_link": group.zoom_link,
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


class StaffPayload(BaseModel):
    telegram_id: int
    full_name: str
    phone: str | None = None
    username: str | None = None


@router.get("/teachers")
async def get_admin_teachers(user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        teachers_res = await session.execute(
            select(User).where(User.role == RoleEnum.teacher, User.is_active == True).order_by(User.id.desc())
        )
        teachers = teachers_res.scalars().all()

        results = []
        for t in teachers:
            grp_res = await session.execute(
                select(Group.id, Group.name).where(Group.teacher_id == t.id, Group.is_active == True)
            )
            assigned_groups = [{"id": r[0], "name": r[1]} for r in grp_res.all()]
            results.append({
                "id": t.id,
                "full_name": t.full_name,
                "username": t.username,
                "phone": t.phone,
                "role": t.role.value if hasattr(t.role, "value") else str(t.role),
                "groups": assigned_groups,
            })
        return results


@router.post("/teachers")
async def create_or_update_teacher(payload: StaffPayload, user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        target = await session.get(User, payload.telegram_id)
        if target:
            target.role = RoleEnum.teacher
            target.full_name = payload.full_name
            if payload.phone:
                target.phone = payload.phone
            if payload.username:
                target.username = payload.username
            target.is_active = True
        else:
            target = User(
                id=payload.telegram_id,
                full_name=payload.full_name,
                phone=payload.phone,
                username=payload.username,
                role=RoleEnum.teacher,
                referral_code=f"TEACH{payload.telegram_id % 10000}",
                is_active=True,
            )
            session.add(target)
        await session.commit()

    return {"status": "success", "message": f"{payload.full_name} o'qituvchi sifatida saqlandi!"}


@router.delete("/teachers/{teacher_id}")
async def delete_admin_teacher(teacher_id: int, user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        target = await session.get(User, teacher_id)
        if not target or target.role != RoleEnum.teacher:
            raise HTTPException(status_code=404, detail="O'qituvchi topilmadi.")

        target.role = RoleEnum.student
        await session.execute(
            update(Group).where(Group.teacher_id == teacher_id).values(teacher_id=None)
        )
        await session.commit()

    return {"status": "success", "message": "O'qituvchi vazifasidan ozod qilindi!"}


@router.get("/admins")
async def get_admin_staff(user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        admins_res = await session.execute(
            select(User).where(User.role.in_([RoleEnum.admin, RoleEnum.manager]), User.is_active == True).order_by(User.id.desc())
        )
        admins = admins_res.scalars().all()

        return [
            {
                "id": a.id,
                "full_name": a.full_name,
                "username": a.username,
                "phone": a.phone,
                "role": a.role.value if hasattr(a.role, "value") else str(a.role),
                "created_at": a.created_at.strftime("%d.%m.%Y") if a.created_at else "-",
            }
            for a in admins
        ]


@router.post("/admins")
async def create_or_update_admin(payload: StaffPayload, user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    admin_user = await add_admin(payload.telegram_id, payload.full_name)

    if payload.phone or payload.username:
        async with async_session() as session:
            target = await session.get(User, payload.telegram_id)
            if target:
                if payload.phone:
                    target.phone = payload.phone
                if payload.username:
                    target.username = payload.username
                await session.commit()

    return {"status": "success", "message": f"{payload.full_name} admin sifatida tayinlandi!"}


@router.delete("/admins/{admin_id}")
async def delete_admin_staff(admin_id: int, user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    if admin_id == user["id"]:
        raise HTTPException(status_code=400, detail="O'zingizdan admin huquqini olib tashlay olmaysiz.")

    await remove_admin(admin_id)
    return {"status": "success", "message": "Admin huquqlari olib tashlandi!"}


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
            group_chat_link=payload.group_chat_link,
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
        group.group_chat_link = payload.group_chat_link
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


@router.post("/payments/{payment_id}/refund")
async def refund_admin_payment(payment_id: int, user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        payment = await session.get(Payment, payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="To'lov topilmadi.")

        if payment.status == PaymentStatusEnum.refunded:
            raise HTTPException(status_code=400, detail="Bu to'lov allaqachon qaytarilgan (refund qilingan).")

        payment.status = PaymentStatusEnum.refunded

        # 1. O'quvchini guruhdan chiqaramiz (Enrollment dropped)
        enr_res = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == payment.student_id,
                Enrollment.group_id == payment.group_id,
                Enrollment.is_active == True,
            )
        )
        enr = enr_res.scalar_one_or_none()
        if enr:
            enr.status = EnrollmentStatusEnum.dropped
            enr.is_active = False
            enr.completed_at = datetime.utcnow()

        # 2. Refund jadvaliga yozamiz
        refund = Refund(
            payment_id=payment.id,
            student_id=payment.student_id,
            group_id=payment.group_id,
            reason="Admin WebApp paneli orqali qaytarildi (Refund)",
            calculated_amount=payment.amount,
            final_amount=payment.amount,
            status="approved",
            approved_by=user["id"],
            processed_at=datetime.utcnow(),
        )
        session.add(refund)

        group = await session.get(Group, payment.group_id)
        group_name = group.name if group else "Guruh"

        await session.commit()

    from main import bot
    try:
        await bot.send_message(
            payment.student_id,
            f"💰 <b>To'lov qaytarildi (Refund)!</b>\n\n"
            f"👥 Guruh: <b>{group_name}</b>\n"
            f"💵 Qaytarilgan summa: <b>{float(payment.amount):,.0f} so'm</b>\n\n"
            f"ℹ️ <i>Siz guruh a'zoligidan chiqarildingiz. Mablag'ni qabul qilish uchun ma'muriyat bilan bog'laning.</i>",
        )
    except Exception:
        pass

    return {"status": "success", "message": "To'lov qaytarildi (Refund) va o'quvchi guruhdan chiqarildi."}


# ==========================================
# 👨‍🏫 O'QITUVCHILARNI BOSHQARISH (TEACHERS)
# ==========================================

class TeacherCreatePayload(BaseModel):
    telegram_id: int
    full_name: str
    phone: str | None = None
    username: str | None = None


@router.get("/teachers")
async def get_admin_teachers(user: dict = Depends(get_current_telegram_user)):
    """Barcha o'qituvchilar ro'yxati va ularga biriktirilgan guruhlar."""
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        res = await session.execute(
            select(User).where(User.role == RoleEnum.teacher).order_by(User.id.desc())
        )
        teachers = res.scalars().all()

        results = []
        for t in teachers:
            grp_res = await session.execute(
                select(Group).where(Group.teacher_id == t.id, Group.is_active == True)
            )
            groups = grp_res.scalars().all()
            results.append({
                "id": t.id,
                "full_name": t.full_name or f"Teacher #{t.id}",
                "username": t.username,
                "phone": t.phone or "-",
                "role": t.role.value if hasattr(t.role, "value") else str(t.role),
                "groups_count": len(groups),
                "groups": [{"id": g.id, "name": g.name} for g in groups],
                "is_active": t.is_active,
                "created_at": t.created_at.strftime("%d.%m.%Y") if t.created_at else "-",
            })
        return results


@router.post("/teachers")
async def add_or_promote_teacher(
    payload: TeacherCreatePayload,
    user: dict = Depends(get_current_telegram_user),
):
    """Yangi o'qituvchi qo'shish yoki mavjud foydalanuvchini o'qituvchi roliga o'tkazish."""
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        t_user = await session.get(User, payload.telegram_id)
        if t_user:
            t_user.role = RoleEnum.teacher
            if payload.full_name:
                t_user.full_name = payload.full_name
            if payload.phone:
                t_user.phone = payload.phone
            if payload.username:
                t_user.username = payload.username
        else:
            t_user = User(
                id=payload.telegram_id,
                full_name=payload.full_name,
                username=payload.username,
                phone=payload.phone,
                role=RoleEnum.teacher,
                referral_code=f"TEACH{payload.telegram_id % 10000}",
                is_active=True,
            )
            session.add(t_user)
        await session.commit()

    return {
        "status": "success",
        "message": f"👨‍🏫 {payload.full_name} muvaffaqiyatli o'qituvchi sifatida biriktirildi!",
    }


@router.delete("/teachers/{teacher_id}")
async def remove_teacher(
    teacher_id: int,
    user: dict = Depends(get_current_telegram_user),
):
    """O'qituvchini vazifasidan ozod qilish (student roliga o'tkazish)."""
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        t_user = await session.get(User, teacher_id)
        if not t_user:
            raise HTTPException(status_code=404, detail="O'qituvchi topilmadi")

        t_user.role = RoleEnum.student
        await session.execute(
            update(Group).where(Group.teacher_id == teacher_id).values(teacher_id=None)
        )
        await session.commit()

    return {"status": "success", "message": "O'qituvchi vazifasidan ozod qilindi."}


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def _send_broadcast_worker(
    user_ids: list[int],
    text: str,
    button_text: str | None = None,
    button_url: str | None = None,
):
    from main import bot
    reply_markup = None
    if button_text and button_url:
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_text, url=button_url)]
        ])

    for uid in user_ids:
        try:
            if reply_markup:
                await bot.send_message(uid, text, parse_mode="HTML", reply_markup=reply_markup)
            else:
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
        if payload.target_role == "student":
            query = select(User.id).where(User.role == RoleEnum.student, User.is_active == True)
        elif payload.target_role == "teacher":
            query = select(User.id).where(User.role == RoleEnum.teacher, User.is_active == True)
        elif payload.target_role in ("IELTS", "CEFR"):
            query = (
                select(User.id.distinct())
                .join(Enrollment, User.id == Enrollment.student_id)
                .join(Group, Enrollment.group_id == Group.id)
                .join(Course, Group.course_id == Course.id)
                .where(Course.type == payload.target_role, Enrollment.is_active == True)
            )
        else:
            query = select(User.id).where(User.is_active == True)

        if payload.level:
            query = query.where(User.level == payload.level)

        res = await session.execute(query)
        user_ids = list(res.scalars().all())

    asyncio.create_task(
        _send_broadcast_worker(
            user_ids=user_ids,
            text=payload.text,
            button_text=payload.button_text,
            button_url=payload.button_url,
        )
    )

    return {
        "status": "success",
        "sent_count": len(user_ids),
        "total_target": len(user_ids),
        "message": f"Xabar {len(user_ids)} ta foydalanuvchiga yuborilmoqda.",
    }


import io
import csv
from fastapi import Response

@router.get("/export/payments-csv")
async def export_payments_csv(user: dict = Depends(get_current_telegram_user)):
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

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "O'quvchi", "Telefon", "Guruh", "Summa (so'm)", "Usul", "Holat", "Sana"])

        for p, student, group in rows:
            writer.writerow([
                p.id,
                student.full_name or student.username or str(student.id),
                student.phone or "-",
                group.name,
                float(p.amount),
                p.method.value if hasattr(p.method, "value") else str(p.method),
                p.status.value if hasattr(p.status, "value") else str(p.status),
                p.created_at.strftime("%d.%m.%Y %H:%M") if p.created_at else "-",
            ])

        csv_content = "\ufeff" + output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=payments_report.csv"},
        )


@router.get("/export/students-csv")
async def export_students_csv(user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        students_res = await session.execute(
            select(User).where(User.role == RoleEnum.student).order_by(User.created_at.desc())
        )
        students = students_res.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Telegram ID", "To'liq Ism", "Username", "Telefon", "Til", "Ro'yxatdan o'tgan sana"])

        for s in students:
            writer.writerow([
                s.id,
                s.full_name or "-",
                f"@{s.username}" if s.username else "-",
                s.phone or "-",
                s.language.value if hasattr(s.language, "value") else str(s.language),
                s.created_at.strftime("%d.%m.%Y") if s.created_at else "-",
            ])

        csv_content = "\ufeff" + output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=students_report.csv"},
        )


# ==========================================
# 7.5.1: TESTLAR VA AI PDF TEST GENERATOR
# ==========================================
from fastapi import UploadFile, File, Form
from backend.models import Test, Question, TestSourceEnum, LevelEnum
from backend.services.ai_test_generator import extract_text_from_pdf, generate_test_from_pdf_text


class TestCreatePayload(BaseModel):
    title_uz: str
    title_ru: str | None = None
    title_en: str | None = None
    certificate_type: str = "IELTS"
    level: str = "B1"
    passing_score: float = 70.0
    time_limit_min: int = 15
    source: str = "manual"
    questions: list[dict]
    is_active: bool = True


@router.get("/tests")
async def get_admin_tests(user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        result = await session.execute(select(Test).order_by(Test.id.desc()))
        tests = result.scalars().all()

        out = []
        for t in tests:
            title_str = t.title.get("uz", "") if isinstance(t.title, dict) else str(t.title)
            out.append({
                "id": t.id,
                "title": t.title,
                "title_display": title_str,
                "certificate_type": t.certificate_type,
                "level": t.level.value if hasattr(t.level, "value") else str(t.level),
                "passing_score": float(t.passing_score),
                "time_limit_min": t.time_limit_min,
                "source": t.source.value if hasattr(t.source, "value") else str(t.source),
                "question_count": len(t.questions) if t.questions else 0,
                "questions": t.questions or [],
                "is_active": t.is_active,
                "created_at": t.created_at.strftime("%d.%m.%Y %H:%M") if t.created_at else "",
            })
        return out


@router.post("/tests/generate-from-pdf")
async def generate_test_from_pdf(
    file: UploadFile = File(...),
    cert_type: str = Form("IELTS"),
    level: str = Form("B1"),
    user: dict = Depends(get_current_telegram_user),
):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Faqat .pdf formatidagi fayllar qabul qilinadi.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Fayl bo'sh.")

    raw_text = extract_text_from_pdf(contents)
    if not raw_text or len(raw_text.strip()) < 10:
        raise HTTPException(status_code=400, detail="PDF faylidan matn ajratib bo'lmadi (matnli PDF ekanligini tekshiring).")

    questions = await generate_test_from_pdf_text(
        raw_text=raw_text,
        cert_type=cert_type,
        level=level,
    )

    warnings = sum(1 for q in questions if q.get("needs_review"))

    return {
        "status": "success",
        "file_name": file.filename,
        "certificate_type": cert_type,
        "level": level,
        "total_questions": len(questions),
        "warning_count": warnings,
        "preview_text": raw_text[:400] + ("..." if len(raw_text) > 400 else ""),
        "questions": questions,
    }


@router.post("/tests")
async def create_admin_test(
    payload: TestCreatePayload,
    user: dict = Depends(get_current_telegram_user),
):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    if not payload.questions:
        raise HTTPException(status_code=400, detail="Testda kamida 1 ta savol bo'lishi kerak.")

    title_dict = {
        "uz": payload.title_uz,
        "ru": payload.title_ru or payload.title_uz,
        "en": payload.title_en or payload.title_uz,
    }

    try:
        level_enum = LevelEnum(payload.level)
    except ValueError:
        level_enum = LevelEnum.B1

    source_enum = TestSourceEnum.ai_pdf if payload.source == "ai_pdf" else TestSourceEnum.manual

    async with async_session() as session:
        test = Test(
            teacher_id=user["id"],
            certificate_type=payload.certificate_type,
            level=level_enum,
            title=title_dict,
            passing_score=payload.passing_score,
            time_limit_min=payload.time_limit_min,
            source=source_enum,
            questions=payload.questions,
            is_active=payload.is_active,
        )
        session.add(test)
        await session.commit()
        await session.refresh(test)

        return {
            "status": "success",
            "message": "Test muvaffaqiyatli yaratildi.",
            "test_id": test.id,
        }


@router.patch("/tests/{test_id}/toggle-active")
async def toggle_test_active(
    test_id: int,
    user: dict = Depends(get_current_telegram_user),
):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        test = await session.get(Test, test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test topilmadi.")

        test.is_active = not test.is_active
        await session.commit()

        return {
            "status": "success",
            "is_active": test.is_active,
            "message": "Test holati o'zgartirildi.",
        }


@router.delete("/tests/{test_id}")
async def delete_admin_test(
    test_id: int,
    user: dict = Depends(get_current_telegram_user),
):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        test = await session.get(Test, test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test topilmadi.")

        await session.delete(test)
        await session.commit()

        return {"status": "success", "message": "Test o'chirildi."}


class SettingsPayload(BaseModel):
    contact_phone: str
    contact_username: str
    address_uz: str
    address_ru: str | None = None
    address_en: str | None = None
    welcome_message_uz: str | None = None
    welcome_message_ru: str | None = None
    welcome_message_en: str | None = None


@router.get("/settings")
async def get_center_settings(user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        result = await session.execute(select(CenterSetting).limit(1))
        settings = result.scalar_one_or_none()
        if not settings:
            settings = CenterSetting(
                id=1,
                contact_phone="+998901234567",
                contact_username="english_center_admin",
                address={
                    "uz": "Toshkent sh., Amir Temur ko'chasi, 12-uy",
                    "ru": "г. Ташкент, ул. Амира Темура, д. 12",
                    "en": "12 Amir Temur street, Tashkent",
                },
                welcome_message={
                    "uz": "Xush kelibsiz! Alpha English Center rasmiy botiga xush kelibsiz. Bu yerda siz kurslarga yozilishingiz, darajangizni aniqlash uchun test topshirishingiz va o'quv natijalaringizni kuzatishingiz mumkin.",
                    "ru": "Добро пожаловать в официальный бот Alpha English Center! Здесь вы можете записаться на курсы, пройти тестирование для определения уровня и отслеживать успеваемость.",
                    "en": "Welcome to the official Alpha English Center bot! Here you can enroll in courses, take placement tests, and track your academic progress."
                },
            )
            session.add(settings)
            await session.commit()
            await session.refresh(settings)

        addr = settings.address if isinstance(settings.address, dict) else {}
        w_msg = settings.welcome_message if isinstance(settings.welcome_message, dict) else {}
        return {
            "contact_phone": settings.contact_phone,
            "contact_username": settings.contact_username,
            "address_uz": addr.get("uz", "Toshkent sh., Amir Temur ko'chasi, 12-uy"),
            "address_ru": addr.get("ru", "г. Ташкент, ул. Амира Темура, д. 12"),
            "address_en": addr.get("en", "12 Amir Temur street, Tashkent"),
            "welcome_message_uz": w_msg.get("uz", "Xush kelibsiz! Alpha English Center rasmiy botiga xush kelibsiz. Bu yerda siz kurslarga yozilishingiz, darajangizni aniqlash uchun test topshirishingiz va o'quv natijalaringizni kuzatishingiz mumkin."),
            "welcome_message_ru": w_msg.get("ru", "Добро пожаловать в официальный бот Alpha English Center! Здесь вы можете записаться на курсы, пройти тестирование для определения уровня и отслеживать успеваемость."),
            "welcome_message_en": w_msg.get("en", "Welcome to the official Alpha English Center bot! Here you can enroll in courses, take placement tests, and track your academic progress."),
        }


@router.put("/settings")
async def update_center_settings(payload: SettingsPayload, user: dict = Depends(get_current_telegram_user)):
    if not await is_admin_or_manager(user["id"]):
        raise HTTPException(status_code=403, detail="Faqat adminlar uchun.")

    async with async_session() as session:
        result = await session.execute(select(CenterSetting).limit(1))
        settings = result.scalar_one_or_none()
        if not settings:
            settings = CenterSetting(id=1)
            session.add(settings)

        clean_username = payload.contact_username.lstrip("@").strip()
        settings.contact_phone = payload.contact_phone.strip()
        settings.contact_username = clean_username
        settings.address = {
            "uz": payload.address_uz.strip(),
            "ru": (payload.address_ru or payload.address_uz).strip(),
            "en": (payload.address_en or payload.address_uz).strip(),
        }
        settings.welcome_message = {
            "uz": (payload.welcome_message_uz or "").strip(),
            "ru": (payload.welcome_message_ru or payload.welcome_message_uz or "").strip(),
            "en": (payload.welcome_message_en or payload.welcome_message_uz or "").strip(),
        }
        settings.updated_by = user["id"]
        settings.updated_at = datetime.utcnow()
        await session.commit()

    return {"status": "success", "message": "Markaz sozlamalari muvaffaqiyatli saqlandi!"}

