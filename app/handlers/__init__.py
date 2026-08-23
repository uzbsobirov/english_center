from aiogram import Dispatcher

from app.handlers import users, groups, channels, teachers

def setup(dp: Dispatcher):
    """
    Botning routerlarini sozlash uchun setup funksiyasi.
    """
    users.setup(dp)  # Foydalanuvchi bilan bog'liq handlerlarni ulash
    teachers.setup(dp)  # O'qituvchi bilan bog'liq handlerlarni ulash