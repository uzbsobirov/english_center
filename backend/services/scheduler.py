"""
Avtomatlashtirilgan eslatmalar va fon cron xizmati (TZ v2.6, 13 & 16.2-bo'limlar).
- 15 daqiqalik muloqot timeouti (support chat avtomatik yopilish) (TZ 16.2)
- Darsdan 3 soat o'tgach uy vazifasi eslatmasi va admin eskalatsiyasi (TZ 7.4)
- Fon asyncio loop orqali xavfsiz va uzluksiz ishlash
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, update, or_

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from backend.database import async_session
from backend.models import (
    SupportChat, SupportChatStatusEnum, SupportChatClosedReasonEnum,
    Group, Enrollment, User, Homework, FreeTrialRequest, FreeTrialStatusEnum
)
from backend.services.user_service import get_admin_ids

logger = logging.getLogger(__name__)
_scheduler_task = None


async def check_support_chat_timeouts(bot):
    """
    TZ 16.2: 15 daqiqa davomida javobsiz qolgan muloqotlarni avtomatik yopish.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=15)

    async with async_session() as session:
        result = await session.execute(
            select(SupportChat).where(
                SupportChat.status == SupportChatStatusEnum.open,
                SupportChat.last_message_at <= cutoff,
            )
        )
        expired_chats = result.scalars().all()

        if not expired_chats:
            return

        notified_students = set()
        notified_admins = set()

        for chat in expired_chats:
            chat.status = SupportChatStatusEnum.closed
            chat.closed_at = datetime.utcnow()
            chat.closed_reason = SupportChatClosedReasonEnum.timeout

            timeout_text = "⏱ Muloqot 15 daqiqa javobsizlik sababli avtomatik yopildi."
            
            # O'quvchiga faqat bir marta xabar berish
            if chat.student_id not in notified_students:
                try:
                    await bot.send_message(chat.student_id, timeout_text)
                    notified_students.add(chat.student_id)
                except Exception:
                    pass

            # Adminga faqat bir marta xabar berish
            if chat.admin_id and (chat.admin_id, chat.student_id) not in notified_admins:
                try:
                    await bot.send_message(chat.admin_id, timeout_text)
                    notified_admins.add((chat.admin_id, chat.student_id))
                except Exception:
                    pass

        await session.commit()
        logger.info(f"[Scheduler] {len(expired_chats)} ta eskirgan support chat yopildi.")


from datetime import datetime, timedelta, date

_reminded_homework_groups = set() # {(group_id, date_str)}


def _is_lesson_today_and_ended_3h_ago(schedule_data) -> bool:
    """
    Guruh dars jadvalini aniq tekshiradi:
    1. Bugun haqiqatdan dars kuni ekanligini (Monday, Tuesday, etc.) tekshiradi.
    2. Dars tugaganidan keyin kamida 3 soat o'tganligini tekshiradi.
    """
    if not schedule_data:
        return False

    now = datetime.now()
    today_weekday_full = now.strftime("%A").lower()  # masalan: 'tuesday'
    today_weekday_short = now.strftime("%a").lower() # masalan: 'tue'

    days = []
    time_str = "18:00"
    duration_min = 90

    if isinstance(schedule_data, dict):
        raw_days = schedule_data.get("days", [])
        if isinstance(raw_days, list):
            days = [str(d).lower() for d in raw_days]
        elif isinstance(raw_days, str):
            days = [str(raw_days).lower()]
        time_str = schedule_data.get("time", "18:00")
        duration_min = int(schedule_data.get("duration_minutes", 90) or 90)

    elif isinstance(schedule_data, list):
        for item in schedule_data:
            if isinstance(item, dict):
                d = str(item.get("day", "")).lower()
                days.append(d)
                if item.get("time"):
                    time_str = item.get("time")
            elif isinstance(item, str):
                days.append(item.lower())

    # 1. Bugun shu guruhning dars kunimi?
    is_today = False
    uz_map = {
        "dushanba": "monday", "seshanba": "tuesday", "chorshanba": "wednesday",
        "payshanba": "thursday", "juma": "friday", "shanba": "saturday", "yakshanba": "sunday",
        "dush": "monday", "sesh": "tuesday", "chor": "wednesday",
        "pay": "thursday", "jum": "friday", "shan": "saturday", "yak": "sunday",
    }
    for d in days:
        if d in (today_weekday_full, today_weekday_short):
            is_today = True
            break
        if uz_map.get(d) in (today_weekday_full, today_weekday_short):
            is_today = True
            break

    if not is_today:
        return False

    # 2. Dars boshlanish va tugash vaqtini hisoblaymiz
    try:
        if ":" in time_str:
            parts = time_str.strip().split(":")
            h, m = int(parts[0]), int(parts[1])
        else:
            h, m = 18, 0
    except Exception:
        h, m = 18, 0

    lesson_start = datetime.combine(now.date(), datetime.min.time()).replace(hour=h, minute=m)
    lesson_end = lesson_start + timedelta(minutes=duration_min)
    reminder_threshold = lesson_end + timedelta(hours=3)

    # 3. Dars tugaganidan keyin kamida 3 soat o'tgan bo'lishi kerak!
    return now >= reminder_threshold


async def check_homework_reminders(bot):
    """
    TZ 7.4 & 13: Dars tugaganidan roppa-rosa 3 soat o'tgach, agar uy vazifasi qo'shilmagan bo'lsa,
    o'qituvchiga eslatma, kiritilmasa bosh adminlarga eskalatsiya xabari yuboriladi.
    """
    today_str = str(date.today())
    now_utc = datetime.utcnow()

    async with async_session() as session:
        groups_res = await session.execute(select(Group).where(Group.is_active == True))
        groups = groups_res.scalars().all()

        admin_ids = await get_admin_ids()

        for g in groups:
            # 1. Bugun dars kuni bo'lmasa yoki dars tugaganiga 3 soat to'lmagan bo'lsa — tashlab o'tamiz
            if not _is_lesson_today_and_ended_3h_ago(g.schedule):
                continue

            # 2. Bugun shu guruh uchun eslatma allaqachon yuborilgan bo'lsa — qayta yubormaymiz
            reminder_key = (g.id, today_str)
            if reminder_key in _reminded_homework_groups:
                continue

            # 3. Bugungi dars uchun uy vazifasi qo'shilganmi tekshiramiz
            hw_res = await session.execute(
                select(Homework).where(
                    Homework.group_id == g.id,
                    (Homework.lesson_date == date.today()) | (Homework.created_at >= now_utc - timedelta(hours=14))
                )
            )
            has_hw = hw_res.scalars().first() is not None

            if not has_hw:
                teacher = await session.get(User, g.teacher_id) if g.teacher_id else None
                # O'qituvchiga eslatma
                if teacher:
                    try:
                        await bot.send_message(
                            teacher.id,
                            f"⚠️ <b>Guruh: {g.name}</b> uchun bugungi darsdan so'ng 3 soat ichida uy vazifasi qo'shilmadi. Qo'shishni unutdingizmi?"
                        )
                    except Exception:
                        pass

                # Admin/Managerlarga eskalatsiya (TZ 7.4)
                for admin_id in admin_ids:
                    try:
                        teacher_name = teacher.full_name if teacher else "Noma'lum"
                        await bot.send_message(
                            admin_id,
                            f"⚠️ <b>{teacher_name}</b> — <b>{g.name}</b> guruhi uchun bugungi darsdan so'ng 3 soat ichida uy vazifasi qo'shmadi."
                        )
                    except Exception:
                        continue

                _reminded_homework_groups.add(reminder_key)


async def check_trial_attendance_reminders(bot):
    """
    Kutilayotgan (invited) sinov darslarining davomati 2+ soat davomida belgilanmagan bo'lsa,
    o'qituvchiga to'g'ridan-to'g'ri yangi eslatma yuborish.
    """
    cutoff = datetime.utcnow() - timedelta(hours=2)
    async with async_session() as session:
        result = await session.execute(
            select(FreeTrialRequest, User, Group)
            .join(User, FreeTrialRequest.student_id == User.id)
            .outerjoin(Group, FreeTrialRequest.group_id == Group.id)
            .where(
                FreeTrialRequest.status == FreeTrialStatusEnum.invited,
                or_(
                    FreeTrialRequest.updated_at <= cutoff,
                    FreeTrialRequest.updated_at.is_(None)
                ),
            )
        )
        pending_trials = result.all()

        for trial, student, group in pending_trials:
            if not trial.teacher_id:
                continue
            grp_name = group.name if group else "Sinov darsi"
            text = (
                f"🔔 <b>Eslatma: Sinov Darsi Davomati</b>\n\n"
                f"👤 <b>O'quvchi:</b> <b>{student.full_name}</b>\n"
                f"👥 <b>Guruh:</b> {grp_name}\n\n"
                f"<i>O'quvchi darsda qatnashdimi? Iltimos, statusni belgilang:</i>"
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🟢 Darsga Keldi", callback_data=f"trial_att_yes:{trial.id}"),
                    InlineKeyboardButton(text="🔴 Kelmadi", callback_data=f"trial_att_no:{trial.id}"),
                ]
            ])
            try:
                await bot.send_message(trial.teacher_id, text, reply_markup=kb)
                trial.updated_at = datetime.utcnow()  # Eslatmani qayta-qayta yubormaslik uchun
            except Exception:
                pass

        if pending_trials:
            await session.commit()


async def _scheduler_loop(bot):
    """Orqa fonda davriy tekshiruvlar."""
    logger.info("[Scheduler] Fon eslatmalari xizmati ishga tushdi.")
    iteration = 0
    while True:
        try:
            # Har 60 soniyada support chat timeoutlarini tekshirish
            await check_support_chat_timeouts(bot)

            # Har 15 daqiqada uy vazifasi va sinov darslari eslatmalarini tekshirish
            if iteration % 15 == 0:
                await check_homework_reminders(bot)
                await check_trial_attendance_reminders(bot)

            iteration += 1
        except Exception as e:
            logger.error(f"[Scheduler] Xatolik: {e}")

        await asyncio.sleep(60)


def start_scheduler(bot):
    """Scheduler ni asyncio fon vazifasi sifatida ishga tushirish."""
    global _scheduler_task
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(_scheduler_loop(bot))
    return _scheduler_task


def stop_scheduler():
    """Schedulerni to'xtatish."""
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        _scheduler_task = None
