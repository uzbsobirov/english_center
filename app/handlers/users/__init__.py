from aiogram import Dispatcher
from .start import router as start_router
from .help import router as help_router
from .courses import router as courses_router
from .profile import router as profile_router
from .homework import router as homework_router
from .contact import router as contact_router
from .referral import router as referral_router
from .schedule import router as schedule_router
from .ranking import router as ranking_router
from .language import router as language_router
from .free_lesson import router as free_lesson_router
from .payments import router as payments_router
from .main_menu import router as main_menu_router


def setup(dp: Dispatcher):
    """
    Foydalanuvchi routerlarini tartibli ulash.
    """
    dp.include_routers(
        start_router,
        help_router,
        courses_router,
        profile_router,
        homework_router,
        contact_router,
        referral_router,
        schedule_router,
        ranking_router,
        language_router,
        free_lesson_router,
        payments_router,
        main_menu_router,
    )