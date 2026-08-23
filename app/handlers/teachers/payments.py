"""
O'qituvchi paneli: naqd to'lov kiritish va qaytarish (refund) so'rovi.
Faqat role='teacher' yoki 'admin' bo'lgan foydalanuvchilar uchun ishlaydi.
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

from backend.database import async_session
from backend.models import User, RoleEnum, Group, Course, Payment, PaymentMethodEnum, PaymentStatusEnum, Refund

from app.state.payments import CashPayment, RefundRequest

router = Router()


async def _is_teacher_or_admin(telegram_id: int) -> bool:
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        return user is not None and user.role in (RoleEnum.teacher, RoleEnum.admin)


@router.message(Command("cash_payment"))
async def start_cash_payment(message: Message, state: FSMContext):
    if not await _is_teacher_or_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat o'qituvchilar uchun.")
        return

    await state.set_state(CashPayment.entering_student_id)
    await message.answer(
        "Naqd to'lov kiritish.\n\nO'quvchining Telegram ID raqamini yuboring:"
    )


@router.message(CashPayment.entering_student_id, F.text)
async def cash_payment_student_id(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Iltimos, faqat raqam yuboring (Telegram ID).")
        return

    student_id = int(message.text.strip())

    async with async_session() as session:
        student = await session.get(User, student_id)

    if student is None:
        await message.answer("Bunday ID bilan foydalanuvchi topilmadi. Qaytadan urinib ko'ring:")
        return

    await state.update_data(student_id=student_id, student_name=student.full_name)
    await state.set_state(CashPayment.entering_group_id)
    await message.answer(f"O'quvchi: {student.full_name}\n\nGuruh ID raqamini yuboring:")


@router.message(CashPayment.entering_group_id, F.text)
async def cash_payment_group_id(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Iltimos, faqat raqam yuboring (Guruh ID).")
        return

    group_id = int(message.text.strip())

    async with async_session() as session:
        group = await session.get(Group, group_id)

    if group is None:
        await message.answer("Bunday ID bilan guruh topilmadi. Qaytadan urinib ko'ring:")
        return

    await state.update_data(group_id=group_id, group_name=group.name)
    await state.set_state(CashPayment.entering_amount)
    await message.answer(f"Guruh: {group.name}\n\nTo'lov summasini kiriting (so'mda, faqat raqam):")


@router.message(CashPayment.entering_amount, F.text)
async def cash_payment_amount(message: Message, state: FSMContext):
    raw = message.text.strip().replace(" ", "").replace(",", "")
    if not raw.isdigit():
        await message.answer("Iltimos, to'g'ri summa kiriting (masalan: 500000).")
        return

    amount = float(raw)
    data = await state.get_data()

    async with async_session() as session:
        payment = Payment(
            student_id=data["student_id"],
            group_id=data["group_id"],
            amount=amount,
            method=PaymentMethodEnum.cash,
            status=PaymentStatusEnum.confirmed,
            confirmed_by=message.from_user.id,
        )
        session.add(payment)
        await session.commit()

    await state.clear()
    await message.answer(
        f"✅ To'lov qabul qilindi!\n\n"
        f"O'quvchi: {data['student_name']}\n"
        f"Guruh: {data['group_name']}\n"
        f"Summa: {amount:,.0f} so'm"
    )



# ============ REFUND (QAYTARISH) ============

@router.message(Command("refund"))
async def start_refund(message: Message, state: FSMContext):
    if not await _is_teacher_or_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat o'qituvchilar/adminlar uchun.")
        return

    await state.set_state(RefundRequest.entering_student_id)
    await message.answer(
        "Qaytarish (refund) so'rovi.\n\nO'quvchining Telegram ID raqamini yuboring:"
    )


@router.message(RefundRequest.entering_student_id, F.text)
async def refund_student_id(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Iltimos, faqat raqam yuboring (Telegram ID).")
        return

    student_id = int(message.text.strip())

    async with async_session() as session:
        student = await session.get(User, student_id)

    if student is None:
        await message.answer("Bunday ID bilan foydalanuvchi topilmadi. Qaytadan urinib ko'ring:")
        return

    await state.update_data(student_id=student_id, student_name=student.full_name)
    await state.set_state(RefundRequest.entering_group_id)
    await message.answer(f"O'quvchi: {student.full_name}\n\nGuruh ID raqamini yuboring:")


@router.message(RefundRequest.entering_group_id, F.text)
async def refund_group_id(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Iltimos, faqat raqam yuboring (Guruh ID).")
        return

    group_id = int(message.text.strip())

    async with async_session() as session:
        group = await session.get(Group, group_id)
        if group is None:
            await message.answer("Bunday ID bilan guruh topilmadi. Qaytadan urinib ko'ring:")
            return

        course = await session.get(Course, group.course_id)

    await state.update_data(
        group_id=group_id,
        group_name=group.name,
        price_per_lesson=float(course.price_per_lesson),
    )
    await state.set_state(RefundRequest.entering_lessons_attended)
    await message.answer(
        f"Guruh: {group.name}\n"
        f"Bir dars narxi: {float(course.price_per_lesson):,.0f} so'm\n\n"
        f"O'quvchi nechta darsga qatnashgan? (raqam kiriting)"
    )


@router.message(RefundRequest.entering_lessons_attended, F.text)
async def refund_lessons_attended(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Iltimos, faqat raqam yuboring.")
        return

    lessons_attended = int(message.text.strip())
    data = await state.get_data()

    async with async_session() as session:
        result = await session.execute(
            select(Payment).where(
                Payment.student_id == data["student_id"],
                Payment.group_id == data["group_id"],
                Payment.status == PaymentStatusEnum.confirmed,
            )
        )
        payments = result.scalars().all()
        total_paid = sum(float(p.amount) for p in payments)

        used_amount = data["price_per_lesson"] * lessons_attended
        refund_amount = max(total_paid - used_amount, 0)

        refund = Refund(
            student_id=data["student_id"],
            group_id=data["group_id"],
            reason=f"{lessons_attended} ta darsga qatnashgan, qolgani qaytariladi",
            calculated_amount=refund_amount,
        )
        session.add(refund)
        await session.commit()

    await state.clear()
    await message.answer(
        f"📋 Qaytarish hisob-kitobi:\n\n"
        f"O'quvchi: {data['student_name']}\n"
        f"Guruh: {data['group_name']}\n"
        f"Jami to'langan: {total_paid:,.0f} so'm\n"
        f"Qatnashgan darslar: {lessons_attended} x {data['price_per_lesson']:,.0f} = {used_amount:,.0f} so'm\n\n"
        f"💰 Qaytariladigan summa: {refund_amount:,.0f} so'm\n\n"
        f"Status: kutilmoqda (admin tasdiqlashi kerak)"
    )