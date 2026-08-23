"""
O'qituvchi paneli: naqd to'lov kiritish va qaytarish (refund) so'rovi.
Faqat role='teacher' yoki 'admin' bo'lgan foydalanuvchilar uchun ishlaydi.

Yaxshilangan oqim:
- Guruh RO'YXATDAN (tugmalar orqali) tanlanadi, ID yozish shart emas
- Guruh narxi avtomatik ko'rsatiladi (kursdan olinadi)
- To'lov qilinganda avtomatik Enrollment (ro'yxatga olish) ham yaratiladi
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from backend.database import async_session
from backend.models import (
    User, RoleEnum, Group, Course, Payment, PaymentMethodEnum, PaymentStatusEnum,
    Enrollment, Refund,
)

from app.state.payments import CashPayment, RefundRequest

router = Router()


async def _is_teacher_or_admin(telegram_id: int) -> bool:
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        return user is not None and user.role in (RoleEnum.teacher, RoleEnum.admin)


async def _get_teacher_groups(teacher_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Group, Course)
            .join(Course, Group.course_id == Course.id)
            .where(Group.teacher_id == teacher_id, Group.is_active == True)
        )
        return result.all()


def _groups_keyboard(groups, callback_prefix: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"{group.name} ({float(course.price):,.0f} so'm)",
            callback_data=f"{callback_prefix}:{group.id}",
        )]
        for group, course in groups
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("cash_payment"))
async def start_cash_payment(message: Message, state: FSMContext):
    if not await _is_teacher_or_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat o'qituvchilar uchun.")
        return

    groups = await _get_teacher_groups(message.from_user.id)
    if not groups:
        await message.answer("Sizga biriktirilgan faol guruh topilmadi.")
        return

    await message.answer(
        "Naqd to'lov kiritish.\n\nGuruhni tanlang:",
        reply_markup=_groups_keyboard(groups, "cash_group"),
    )


@router.callback_query(F.data.startswith("cash_group:"))
async def cash_payment_group_selected(callback: CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        group = await session.get(Group, group_id)
        course = await session.get(Course, group.course_id)

    await state.update_data(
        group_id=group_id,
        group_name=group.name,
        course_price=float(course.price),
    )
    await state.set_state(CashPayment.entering_student_id)
    await callback.message.edit_text(
        f"Guruh: {group.name}\n"
        f"Kurs narxi: {float(course.price):,.0f} so'm\n\n"
        f"O'quvchining Telegram ID raqamini yuboring:"
    )
    await callback.answer()


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

    data = await state.get_data()
    await state.update_data(student_id=student_id, student_name=student.full_name)

    price = data["course_price"]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"To'liq narx: {price:,.0f} so'm", callback_data="cash_amount:full")],
        [InlineKeyboardButton(text="Boshqa summa", callback_data="cash_amount:custom")],
    ])
    await message.answer(
        f"O'quvchi: {student.full_name}\n\nTo'lov summasini tanlang:",
        reply_markup=keyboard,
    )


@router.callback_query(F.data == "cash_amount:full")
async def cash_payment_full_amount(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await _save_cash_payment(callback.from_user.id, data, data["course_price"])
    await callback.message.edit_text(
        f"✅ To'lov qabul qilindi!\n\n"
        f"O'quvchi: {data['student_name']}\n"
        f"Guruh: {data['group_name']}\n"
        f"Summa: {data['course_price']:,.0f} so'm"
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cash_amount:custom")
async def cash_payment_custom_amount(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CashPayment.entering_amount)
    await callback.message.edit_text("To'lov summasini kiriting (so'mda, faqat raqam):")
    await callback.answer()


@router.message(CashPayment.entering_amount, F.text)
async def cash_payment_amount(message: Message, state: FSMContext):
    raw = message.text.strip().replace(" ", "").replace(",", "")
    if not raw.isdigit():
        await message.answer("Iltimos, to'g'ri summa kiriting (masalan: 500000).")
        return

    amount = float(raw)
    data = await state.get_data()
    await _save_cash_payment(message.from_user.id, data, amount)

    await state.clear()
    await message.answer(
        f"✅ To'lov qabul qilindi!\n\n"
        f"O'quvchi: {data['student_name']}\n"
        f"Guruh: {data['group_name']}\n"
        f"Summa: {amount:,.0f} so'm"
    )


async def _save_cash_payment(teacher_id: int, data: dict, amount: float):
    async with async_session() as session:
        payment = Payment(
            student_id=data["student_id"],
            group_id=data["group_id"],
            amount=amount,
            method=PaymentMethodEnum.cash,
            status=PaymentStatusEnum.confirmed,
            confirmed_by=teacher_id,
        )
        session.add(payment)

        result = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == data["student_id"],
                Enrollment.group_id == data["group_id"],
            )
        )
        existing_enrollment = result.scalar_one_or_none()
        if existing_enrollment is None:
            session.add(Enrollment(
                student_id=data["student_id"],
                group_id=data["group_id"],
            ))

        await session.commit()


@router.message(Command("refund"))
async def start_refund(message: Message, state: FSMContext):
    if not await _is_teacher_or_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat o'qituvchilar/adminlar uchun.")
        return

    groups = await _get_teacher_groups(message.from_user.id)
    if not groups:
        await message.answer("Sizga biriktirilgan faol guruh topilmadi.")
        return

    await message.answer(
        "Qaytarish (refund) so'rovi.\n\nGuruhni tanlang:",
        reply_markup=_groups_keyboard(groups, "refund_group"),
    )


@router.callback_query(F.data.startswith("refund_group:"))
async def refund_group_selected(callback: CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        group = await session.get(Group, group_id)
        course = await session.get(Course, group.course_id)

    await state.update_data(
        group_id=group_id,
        group_name=group.name,
        price_per_lesson=float(course.price_per_lesson),
    )
    await state.set_state(RefundRequest.entering_student_id)
    await callback.message.edit_text(
        f"Guruh: {group.name}\n"
        f"Bir dars narxi: {float(course.price_per_lesson):,.0f} so'm\n\n"
        f"O'quvchining Telegram ID raqamini yuboring:"
    )
    await callback.answer()


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
    await state.set_state(RefundRequest.entering_lessons_attended)
    await message.answer("O'quvchi nechta darsga qatnashgan? (raqam kiriting)")


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