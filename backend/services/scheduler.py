"""
Avtomatlashtirilgan eslatmalar va fon cron xizmati (TZ v2.6, 13 & 16.2-bo'limlar).
- 15 daqiqalik muloqot timeouti (support chat avtomatik yopilish) (TZ 16.2)
- Darsdan 3 soat o'tgach uy vazifasi eslatmasi va admin eskalatsiyasi (TZ 7.4)
- Fon asyncio loop orqali xavfsiz va uzluksiz ishlash
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, update

from backend.database import async_session
from backend.models import (
    SupportChat, SupportChatStatusEnum, SupportChatClosedReasonEnum,
    Group, Enrollment, User, Homework
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

        for chat in expired_chats:
            chat.status = SupportChatStatusEnum.closed
            chat.closed_at = datetime.utcnow()
            chat.closed_reason = SupportChatClosedReasonEnum.timeout

            timeout_text = "⏱ Muloqot 15 daqiqa javobsizlik sababli avtomatik yopildi."
            # O'quvchiga xabar
            try:
                await bot.send_message(chat.student_id, timeout_text)
            except Exception:
                pass
            # Adminga xabar
            if chat.admin_id:
                try:
                    await bot.send_message(chat.admin_id, timeout_text)
                except Exception:
                    pass

        if expired_chats:
            await session.commit()
            logger.info(f"[Scheduler] {len(expired_chats)} ta eskirgan support chat yopildi.")


async def check_homework_reminders(bot):
    """
    TZ 7.4 & 13: Dars tugaganidan 3 soat o'tgach, agar uy vazifasi qo'shilmagan bo'lsa,
    o'qituvchiga eslatma, hali ham qo'shilmasa admin/managerga eskalatsiya.
    """
    async with async_session() as session:
        groups_res = await session.execute(select(Group).where(Group.is_active == True))
        groups = groups_res.scalars().all()

        admin_ids = await get_admin_ids()

        for g in groups:
            # Bugun shu guruhga uy vazifasi qo'shilganmi tekshiramiz
            hw_res = await session.execute(
                select(Homework).where(
                    Homework.group_id == g.id,
                    Homework.created_at >= datetime.utcnow() - timedelta(hours=4)
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
                            f"⚠️ <b>Guruh: {g.name}</b> uchun uy vazifasi qo'shilmagan. Qo'shishni unutdingizmi?"
                        )
                    except Exception:
                        pass

                # Admin/Managerlarga eskalatsiya (TZ 7.4)
                for admin_id in admin_ids:
                    try:
                        teacher_name = teacher.full_name if teacher else "Noma'lum"
                        await bot.send_message(
                            admin_id,
                            f"⚠️ <b>{teacher_name}</b> — <b>{g.name}</b> guruhi uchun darsdan keyin 3 soat ichida uy vazifasi qo'shmadi."
                        )
                    except Exception:
                        continue


async def _scheduler_loop(bot):
    """Orqa fonda davriy tekshiruvlar."""
    logger.info("[Scheduler] Fon eslatmalari xizmati ishga tushdi.")
    iteration = 0
    while True:
        try:
            # Har 60 soniyada support chat timeoutlarini tekshirish
            await check_support_chat_timeouts(bot)

            # Har 15 daqiqada (15 ta tsiklda) uy vazifasi eslatmalarini tekshirish
            if iteration % 15 == 0:
                await check_homework_reminders(bot)

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
