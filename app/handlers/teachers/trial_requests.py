"""
O'qituvchi tomonidan free-dars so'rovini qabul qilish.
7.1.1: 'Birinchi bosgan g'olib' mexanizmi - SQL darajasidagi ATOMIK UPDATE orqali
amalga oshiriladi, shunda bir nechta o'qituvchi bir vaqtda bossa ham faqat
bittasi muvaffaqiyatli bo'ladi (race condition oldini olinadi).
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import update, select

from backend.database import async_session
from backend.models import FreeTrialRequest, FreeTrialStatusEnum, User

router = Router()


@router.callback_query(F.data.startswith("trial_accept:"))
async def accept_trial(callback: CallbackQuery):
    trial_id = int(callback.data.split(":")[1])
    teacher_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(
            update(FreeTrialRequest)
            .where(
                FreeTrialRequest.id == trial_id,
                FreeTrialRequest.status == FreeTrialStatusEnum.pending,
            )
            .values(status=FreeTrialStatusEnum.invited, teacher_id=teacher_id)
        )
        await session.commit()

        won = result.rowcount > 0

        if not won:
            await callback.answer(
                "Kechirasiz, bu so'rovni boshqa o'qituvchi allaqachon qabul qilgan.",
                show_alert=True,
            )
            return

        trial = await session.get(FreeTrialRequest, trial_id)
        student = await session.get(User, trial.student_id)
        teacher = await session.get(User, teacher_id)

    from main import bot

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ Siz ushbu so'rovni qabul qildingiz!",
        reply_markup=None,
    )

    if student is not None:
        try:
            await bot.send_message(
                student.id,
                f"🎉 Sizga o'qituvchi tayinlandi: {teacher.full_name}!\n"
                f"Tez orada siz bilan bog'lanishadi.",
            )
        except Exception:
            pass

    await callback.answer("Muvaffaqiyatli qabul qilindi!")