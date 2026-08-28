from aiogram.fsm.state import State, StatesGroup

class HomeworkState(StatesGroup):
    choosing_group = State()
    entering_title = State()
    entering_description = State()
    uploading_file = State()
