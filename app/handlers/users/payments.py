"""
O'quvchi tomonidan to'lov so'rovi yuborish.
Oqim: o'quvchi guruh tanlaydi -> usul tanlaydi (naqd/online) -> so'rov yaratiladi
-> o'qituvchiga/adminlarga xabar boradi -> ular tasdiqlaydi -> Enrollment yaratiladi.
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, update

from data.config import env
from backend.database import async_session
from backend.models import (
    Group, Course, Payment, PaymentMethodEnum, PaymentStatusEnum,
    Enrollment, User,
)

router = Router()

PAY_BUTTON_TEXTS = {"💳 To'lov qilish", "💳 Оплатить", "💳 Make payment"}


async def _get_active_groups():
    async with async_session() as session:
        result = await session.execute(
            select(Group, Course)
            .join(Course, Group.course_id == Course.id)
            .where(Group.is_active == True)
        )
        return result.all()


@router.message(Command("pay"))
@router.message(F.text.in_(PAY_BUTTON_TEXTS))
async def start_payment(message: Message, state: FSMContext):
    groups = await _get_active_groups()
    if not groups:
        await message.answer("Hozircha faol guruhlar mavjud emas.")
        return

    buttons = [
        [InlineKeyboardButton(
            text=f"{group.name} ({float(course.price):,.0f} so'm)",
            callback_data=f"pay_group:{group.id}",
        )]
        for group, course in groups
    ]
    await message.answer(
        "To'lov qilmoqchi bo'lgan guruhingizni tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("pay_group:"))
async def payment_group_selected(callback: CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        group = await session.get(Group, group_id)
        course = await session.get(Course, group.course_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Naqd to'lov", callback_data=f"pay_method:cash:{group_id}")],
        [InlineKeyboardButton(text="🌐 Online (tez orada)", callback_data="pay_method:online")],
    ])
    await callback.message.edit_text(
        f"Guruh: {group.name}\n"
        f"Narx: {float(course.price):,.0f} so'm\n\n"
        f"To'lov usulini tanlang:",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == "pay_method:online")
async def payment_online_placeholder(callback: CallbackQuery):
    await callback.answer(
        "Online to'lov (Payme/Click/Uzum) tez orada ishga tushadi. Hozircha naqd to'lovdan foydalaning.",
        show_alert=True,
    )


@router.callback_query(F.data.startswith("pay_method:cash:"))
async def payment_cash_requested(callback: CallbackQuery):
    group_id = int(callback.data.split(":")[2])
    student_id = callback.from_user.id
    student_name = callback.from_user.full_name

    async with async_session() as session:
        group = await session.get(Group, group_id)
        course = await session.get(Course, group.course_id)

        payment = Payment(
            student_id=student_id,
            group_id=group_id,
            amount=course.price,
            method=PaymentMethodEnum.cash,
            status=PaymentStatusEnum.pending,
        )
        session.add(payment)
        await session.flush()
        payment_id = payment.id
        await session.commit()

        teacher = await session.get(User, group.teacher_id)

    await callback.message.edit_text(
        f"✅ So'rovingiz yuborildi!\n\n"
        f"Guruh: {group.name}\n"
        f"Summa: {float(course.price):,.0f} so'm\n\n"
        f"Iltimos, naqd pulni o'qituvchingizga topshiring. "
        f"To'lov qabul qilingach, tasdiqlanadi."
    )
    await callback.answer()

    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_payment:{payment_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_payment:{payment_id}"),
    ]])
    text = (
        f"💵 Yangi naqd to'lov so'rovi!\n\n"
        f"O'quvchi: {student_name}\n"
        f"Guruh: {group.name}\n"
        f"Summa: {float(course.price):,.0f} so'm\n\n"
        f"Pulni qabul qilgach, tasdiqlang:"
    )

    from main import bot
    recipients = [group.teacher_id] if teacher is not None else []
    if not recipients:
        recipients = [int(a) for a in env.list("ADMINS")]

    for recipient_id in recipients:
        try:
            await bot.send_message(recipient_id, text, reply_markup=confirm_keyboard)
        except Exception:
            continue


@router.callback_query(F.data.startswith("confirm_payment:"))
async def confirm_payment(callback: CallbackQuery):
    payment_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        result = await session.execute(
            update(Payment)
            .where(Payment.id == payment_id, Payment.status == PaymentStatusEnum.pending)
            .values(status=PaymentStatusEnum.confirmed, confirmed_by=callback.from_user.id)
        )
        await session.commit()

        if result.rowcount == 0:
            await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
            return

        payment = await session.get(Payment, payment_id)

        existing = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == payment.student_id,
                Enrollment.group_id == payment.group_id,
            )
        )
        if existing.scalar_one_or_none() is None:
            session.add(Enrollment(student_id=payment.student_id, group_id=payment.group_id))
            await session.commit()

    await callback.message.edit_text(callback.message.text + "\n\n✅ Tasdiqlandi.")
    await callback.answer("Tasdiqlandi!")

    from main import bot
    try:
        await bot.send_message(
            payment.student_id,
            f"✅ To'lovingiz tasdiqlandi! Endi siz guruhga rasman yozildingiz.",
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("reject_payment:"))
async def reject_payment(callback: CallbackQuery):
    payment_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        result = await session.execute(
            update(Payment)
            .where(Payment.id == payment_id, Payment.status == PaymentStatusEnum.pending)
            .values(status=PaymentStatusEnum.rejected)
        )
        await session.commit()

        if result.rowcount == 0:
            await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
            return

        payment = await session.get(Payment, payment_id)

    await callback.message.edit_text(callback.message.text + "\n\n❌ Rad etildi.")
    await callback.answer("Rad etildi.")

    from main import bot
    try:
        await bot.send_message(
            payment.student_id,
            "❌ Afsuski, to'lov so'rovingiz rad etildi. Iltimos, o'qituvchi bilan bog'laning.",
        )
    except Exception:
        pass