from aiogram import Bot
from aiogram.types import BotCommand

async def set_bot_commands(bot: Bot):
    """
    Bot komandalar menyusi - minimalist va professional darajada.
    Barcha kundalik amallar 100% reply & inline tugmalar orqali boshqariladi.
    """
    commands = [
        BotCommand(command="start", description="🚀 Asosiy Menyu"),
    ]
    await bot.set_my_commands(commands=commands)