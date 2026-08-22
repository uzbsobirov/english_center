from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    """
    Ro'yxatdan o'tish jarayoni:
    til tanlash -> ism -> telefon -> tugadi (asosiy menyu)
    """
    choosing_language = State()
    entering_name = State()
    entering_phone = State()