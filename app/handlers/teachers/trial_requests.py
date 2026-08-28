"""
O'qituvchi tomonidan free-dars so'rovini qabul qilish.
7.1.1: 'Birinchi bosgan g'olib' mexanizmi - SQL darajasidagi ATOMIK UPDATE orqali
amalga oshiriladi, shunda bir nechta o'qituvchi bir vaqtda bossa ham faqat
bittasi muvaffaqiyatli bo'ladi (race condition oldini olinadi).
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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
        student = await session.get(User, trial.student_id) if trial else None
        teacher = await session.get(User, teacher_id)

    from main import bot

    if student:
        student_username_str = f"@{student.username}" if student.username else "Mavjud emas"
        student_link = f"<a href='tg://user?id={student.id}'>{student.full_name}</a>"
        phone_str = student.phone or "Kiritilmagan"

        teacher_card_text = (
            f"✅ <b>Siz free-dars so'rovini qabul qildingiz!</b>\n\n"
            f"👤 <b>O'quvchi:</b> {student_link}\n"
            f"📱 <b>Telefon:</b> {phone_str}\n"
            f"🌐 <b>Username:</b> {student_username_str}\n"
            f"🆔 <b>Telegram ID:</b> <code>{student.id}</code>\n\n"
            f"<i>Iltimos, o'quvchi bilan bog'lanib, bepul sinov darsi vaqti va joyini kelishib oling.</i>"
        )
        teacher_buttons = []
        if student.username:
            teacher_buttons.append([InlineKeyboardButton(text="💬 O'quvchiga yozish", url=f"https://t.me/{student.username}")])
        else:
            teacher_buttons.append([InlineKeyboardButton(text="👤 O'quvchi Profilini Ochish", url=f"tg://user?id={student.id}")])

        await callback.message.edit_text(
            teacher_card_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=teacher_buttons),
        )

        # O'quvchiga xabar
        teacher_name = teacher.full_name if teacher else callback.from_user.full_name
        teacher_username = f"@{teacher.username}" if teacher and teacher.username else ""
        teacher_link = f"<a href='tg://user?id={teacher_id}'>{teacher_name}</a>"

        student_msg = (
            f"🎉 <b>Tabriklaymiz! Bepul sinov darsi so'rovingiz qabul qilindi.</b>\n\n"
            f"👨‍🏫 <b>Sizning o'qituvchingiz:</b> {teacher_link} {teacher_username}\n\n"
            f"O'qituvchingiz tez orada siz bilan bog'lanib, dars vaqti va joyini ma'lum qiladi."
        )
        student_buttons = []
        if teacher and teacher.username:
            student_buttons.append([InlineKeyboardButton(text="👨‍🏫 O'qituvchiga yozish", url=f"https://t.me/{teacher.username}")])
        else:
            student_buttons.append([InlineKeyboardButton(text="👨‍🏫 O'qituvchi Profilini Ochish", url=f"tg://user?id={teacher_id}")])

        try:
            await bot.send_message(
                student.id,
                student_msg,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=student_buttons),
            )
        except Exception:
            pass
    else:
        await callback.message.edit_text("✅ Siz ushbu so'rovni qabul qildingiz!")

    await callback.answer("Muvaffaqiyatli qabul qilindi!")