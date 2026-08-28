from aiogram.fsm.state import State, StatesGroup

class SupportState(StatesGroup):
    writing_question = State()
    in_chat = State()
