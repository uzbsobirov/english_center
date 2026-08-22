import asyncio
from data import config

from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram import Bot, Dispatcher, Router
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore


import middlewares
from app import handlers
from app.utils.notify_admins import notify_admins
from app.utils.set_bot_commands import set_bot_commands
from app.utils.misc.logging import setup_logger

from app.utils.i18n_manager import UserManager

router = Router()

bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# i18n: locales/{locale}/LC_MESSAGES/bot.ftl fayllaridan o'qiydi
i18n_middleware = I18nMiddleware(
    core=FluentRuntimeCore(path="locales/{locale}/LC_MESSAGES"),
    manager=UserManager(),
    default_locale="uz",
)

async def main():
    """
    Asosiy funktsiya, botni ishga tushurish va handlerlarni sozlash
    """
    handlers.setup(dp)
    i18n_middleware.setup(dispatcher=dp)
    setup_logger()
    router.message.middleware(middleware=middlewares)
    await set_bot_commands(bot)
    await notify_admins(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        # Bot sessiyasini tozalash
        asyncio.run(bot.session.close())