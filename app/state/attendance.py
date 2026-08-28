from aiogram.fsm.state import State, StatesGroup

class AttendanceState(StatesGroup):
    choosing_group = State()
    marking_students = State()
