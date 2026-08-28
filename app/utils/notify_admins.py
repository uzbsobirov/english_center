from aiogram import Bot
from aiogram.utils.markdown import hbold

from data.config import ADMINS
from backend.services.user_service import get_admin_ids


async def notify_admins(bot: Bot) -> None:
    """
    Adminlarga bot ishga tushgani haqida xabar yuborish (TZ 18 bo'yicha bazadan olinadi).
    """
    try:
        admin_ids = await get_admin_ids()
    except Exception:
        admin_ids = []

    if not admin_ids:
        admin_ids = [int(a) for a in ADMINS if str(a).isdigit()]

    for admin_id in admin_ids:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=f"{hbold('🤖 English Center Bot ishga tushdi!')}"
            )
        except Exception as e:
            print(f"Admin {admin_id} ga xabar yuborishda xato: {e}")