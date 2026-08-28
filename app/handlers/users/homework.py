"""
📋 Uy Vazifam bo'limi (TZ v2.6, 16.4-bo'lim).
- Guruhda o'qimasa: «Siz hozircha hech qaysi kursda o'qimayapsiz» + Free dars tugmasi
- Guruhda o'qisa: Faol uy vazifalari ro'yxati, muddati, fayl biriktirmalari
"""
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_i18n import I18nContext
from sqlalchemy import select

from backend.database import async_session
from backend.models import Enrollment, Homework, Group

router = Router()

HOMEWORK_BUTTON_TEXTS = {"📋 Uy Vazifam", "📋 Домашнее задание", "📋 Homework"}


@router.message(F.text.in_(HOMEWORK_BUTTON_TEXTS))
async def show_homework(message: Message, i18n: I18nContext):
    user_id = message.from_user.id

    async with async_session() as session:
        # O'quvchining faol guruhini topamiz
        enrollment_res = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == user_id,
                Enrollment.is_active == True,
            ).order_by(Enrollment.enrolled_at.desc())
        )
        enrollment = enrollment_res.scalar_one_or_none()

        if not enrollment:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📝 Free darsga yozilish", callback_data="start_free_trial_flow")]
            ])
            await message.answer(
                "📚 <b>Siz hozircha hech qaysi guruhda o'qimayapsiz.</b>\n\n"
                "Kurslarimizga a'zo bo'lish uchun bepul sinov darsiga yoziling:",
                reply_markup=keyboard,
            )
            return

        group = await session.get(Group, enrollment.group_id)

        # Guruhning uy vazifalarini olamiz
        hw_res = await session.execute(
            select(Homework).where(
                Homework.group_id == enrollment.group_id
            ).order_by(Homework.created_at.desc()).limit(5)
        )
        homeworks = hw_res.scalars().all()

    if not homeworks:
        await message.answer(
            f"📋 <b>{group.name if group else 'Guruh'}</b> bo'yicha hozircha yangi uy vazifalari yo'q. Baraka toping! 🎉"
        )
        return

    text = [f"📋 <b>{group.name} guruhi uy vazifalari:</b>\n"]
    for idx, hw in enumerate(homeworks, 1):
        due_str = hw.due_at.strftime("%d.%m.%Y %H:%M") if hw.due_at else "Belgilanmagan"
        text.append(
            f"<b>{idx}. {hw.title}</b>\n"
            f"📝 {hw.description or 'Qo\'shimcha izoh yo\'q'}\n"
            f"⏳ <b>Topshirish muddati:</b> {due_str}\n"
        )

    await message.answer("\n".join(text))
