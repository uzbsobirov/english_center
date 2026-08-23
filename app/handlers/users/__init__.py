from aiogram import Dispatcher
from .start import router as user_router
from .help import router as help_router
from .main_menu import router as main_menu_router
from .payments import router as payments_router

def setup(dp: Dispatcher):
    """
    Botning routerlarini ulash uchun setup funksiyasi.
    """
    dp.include_routers(
        user_router,
        help_router,
        payments_router,
        main_menu_router,
    )