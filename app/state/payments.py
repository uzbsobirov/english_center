from aiogram.fsm.state import State, StatesGroup


class CashPayment(StatesGroup):
    """O'qituvchi naqd to'lovni kiritish jarayoni."""
    entering_student_id = State()
    entering_group_id = State()
    entering_amount = State()


class RefundRequest(StatesGroup):
    """Qaytarish (refund) so'rovini kiritish jarayoni."""
    entering_student_id = State()
    entering_group_id = State()
    entering_lessons_attended = State()