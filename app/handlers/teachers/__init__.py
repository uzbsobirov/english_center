from aiogram import Dispatcher
from .trial_requests import router as trial_requests_router

def setup(dp: Dispatcher):
    """
    O'qituvchi bilan bog'liq routerlarni ulash uchun setup funksiyasi.
    """
    dp.include_routers(
        trial_requests_router,
    )