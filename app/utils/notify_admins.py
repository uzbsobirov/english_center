from aiogram import Bot
from aiogram.utils.markdown import hbold
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from data.config import ADMINS
from backend.services.user_service import get_admin_ids


async def notify_admins(bot: Bot) -> None:
    """
    Adminlarga bot ishga tushgani haqida xabar yuborish (TZ 18 bo'yicha bazadan olinadi).
    Faqat haqiqiy Telegram chatiga ega bo'lgan adminlarga yuboriladi (test hisoblari filtrlanadi).
    """
    try:
        admin_ids = await get_admin_ids()
    except Exception:
        admin_ids = []

    real_config_admins = [int(a) for a in ADMINS if str(a).isdigit()]

    # Faqat haqiqiy Telegram ID larni tanlaymiz (synthetic test akkauntlar 7100000000+ va 999999999 chiqarib tashlanadi)
    target_admins = set(real_config_admins)
    for aid in admin_ids:
        if aid < 7000000000 and aid != 999999999:
            target_admins.add(aid)

    for admin_id in target_admins:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=f"{hbold('🤖 English Center Bot ishga tushdi!')}"
            )
        except (TelegramBadRequest, TelegramForbiddenError):
            pass
        except Exception as e:
            print(f"Admin {admin_id} ga bildirishnoma yuborilmadi: {e}")