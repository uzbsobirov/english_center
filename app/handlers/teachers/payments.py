"""
O'qituvchi va Admin paneli: naqd to'lov kiritish va qaytarish (refund) boshqaruvi (TZ v2.6, 7.2, 9, 12).
Faqat role in ('teacher', 'admin', 'manager') bo'lgan foydalanuvchilar uchun ishlaydi.
- Guruh tanlanganda o'quvchilar ro'yxati inline tugmalar ko'rinishida chiqadi (ID yozish shart emas)
- 5% referal chegirma faqat to'liq to'lov to'langandagina beriladi
"""
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, func, update

from backend.database import async_session
from backend.models import (
    User, RoleEnum, Group, Course, Payment, PaymentMethodEnum, PaymentStatusEnum,
    Enrollment, EnrollmentStatusEnum, Refund, Attendance, AttendanceStatusEnum, ReferralBonus,
    FreeTrialRequest,
)
from app.state.payments import CashPayment, RefundRequest
from backend.services.gamification import award_badge_if_eligible
from backend.utils.formatters import format_schedule

router = Router()

_format_schedule = format_schedule


async def _is_teacher_or_admin(telegram_id: int) -> bool:
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        return user is not None and user.role in (RoleEnum.teacher, RoleEnum.admin, RoleEnum.manager)


async def _get_teacher_groups(teacher_id: int):
    async with async_session() as session:
        user = await session.get(User, teacher_id)
        if user and user.role in (RoleEnum.admin, RoleEnum.manager):
            result = await session.execute(
                select(Group, Course)
                .join(Course, Group.course_id == Course.id)
                .where(Group.is_active == True)
            )
        else:
            result = await session.execute(
                select(Group, Course)
                .join(Course, Group.course_id == Course.id)
                .where(Group.teacher_id == teacher_id, Group.is_active == True)
            )
        return result.all()


def _groups_keyboard(groups, callback_prefix: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"👥 {group.name} ({float(course.price):,.0f} so'm)",
            callback_data=f"{callback_prefix}:{group.id}",
        )]
        for group, course in groups
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


from app.keyboards.admin_menu import ALL_CASH_BUTTONS, ALL_REFUND_BUTTONS


@router.message(Command("cash_payment"))
@router.message(F.text.in_(ALL_CASH_BUTTONS))
async def start_cash_payment(message: Message, state: FSMContext):
    if not await _is_teacher_or_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat o'qituvchilar va adminlar uchun.")
        return

    groups = await _get_teacher_groups(message.from_user.id)
    if not groups:
        await message.answer("Sizga biriktirilgan faol guruh topilmadi.")
        return

    await message.answer(
        "💵 <b>Naqd to'lov qabul qilish</b>\n\nGuruhni tanlang:",
        reply_markup=_groups_keyboard(groups, "cash_group"),
    )


@router.callback_query(F.data.startswith("cash_group:"))
async def cash_payment_group_selected(callback: CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        group = await session.get(Group, group_id)
        course = await session.get(Course, group.course_id)

        # 1. Shu guruhdagi mavjud o'quvchilar
        enr_res = await session.execute(
            select(User)
            .join(Enrollment, Enrollment.student_id == User.id)
            .where(Enrollment.group_id == group_id)
        )
        enrolled_students = enr_res.scalars().all()

        # 2. Shu guruhga free-trial so'ragan o'quvchilar
        trial_res = await session.execute(
            select(User)
            .join(FreeTrialRequest, FreeTrialRequest.student_id == User.id)
            .where(FreeTrialRequest.group_id == group_id)
        )
        trial_students = trial_res.scalars().all()

        # 3. Barcha o'quvchilar (agar guruhda hali hech kim bo'lmasa)
        all_students_res = await session.execute(
            select(User).where(User.role == RoleEnum.student).order_by(User.created_at.desc()).limit(10)
        )
        recent_students = all_students_res.scalars().all()

    # Birlashtiramiz (takrorlanishsiz)
    student_dict = {}
    for s in enrolled_students + trial_students + recent_students:
        student_dict[s.id] = s

    await state.update_data(
        group_id=group_id,
        group_name=group.name,
        course_price=float(course.price),
    )

    buttons = []
    for s_id, s in student_dict.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {s.full_name}" + (f" (@{s.username})" if s.username else ""),
                callback_data=f"cash_student:{s_id}",
            )
        ])

    buttons.append([InlineKeyboardButton(text="⌨️ Telegram ID orqali kiritish", callback_data="cash_manual_id")])
    buttons.append([InlineKeyboardButton(text="◀️ Ortga", callback_data="cash_back_groups")])

    await callback.message.edit_text(
        f"👥 <b>Guruh:</b> {group.name}\n"
        f"💵 <b>Kurs narxi:</b> {float(course.price):,.0f} so'm\n\n"
        f"To'lov qilayotgan o'quvchini tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data == "cash_back_groups")
async def cash_back_groups_callback(callback: CallbackQuery, state: FSMContext):
    groups = await _get_teacher_groups(callback.from_user.id)
    await callback.message.edit_text(
        "💵 <b>Naqd to'lov qabul qilish</b>\n\nGuruhni tanlang:",
        reply_markup=_groups_keyboard(groups, "cash_group"),
    )
    await callback.answer()


@router.callback_query(F.data == "cash_manual_id")
async def cash_manual_id_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CashPayment.entering_student_id)
    await callback.message.edit_text("O'quvchining Telegram ID raqamini kiriting:")
    await callback.answer()


@router.callback_query(F.data.startswith("cash_student:"))
async def cash_student_selected(callback: CallbackQuery, state: FSMContext):
    student_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        student = await session.get(User, student_id)

    if not student:
        await callback.answer("O'quvchi topilmadi.", show_alert=True)
        return

    data = await state.get_data()
    await state.update_data(student_id=student_id, student_name=student.full_name)

    price = data["course_price"]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"To'liq narx: {price:,.0f} so'm", callback_data="cash_amount:full")],
        [InlineKeyboardButton(text="Boshqa summa kiritish", callback_data="cash_amount:custom")],
        [InlineKeyboardButton(text="◀️ Ortga", callback_data=f"cash_group:{data['group_id']}")],
    ])
    await callback.message.edit_text(
        f"👤 <b>O'quvchi:</b> {student.full_name} (ID: <code>{student_id}</code>)\n"
        f"👥 <b>Guruh:</b> {data['group_name']}\n\n"
        f"To'lov summasini tanlang:",
        reply_markup=keyboard,
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
        await message.answer("Bunday ID bilan foydalanuvchi topilmadi. Qaytadan kiriting:")
        return

    data = await state.get_data()
    await state.update_data(student_id=student_id, student_name=student.full_name)

    price = data["course_price"]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"To'liq narx: {price:,.0f} so'm", callback_data="cash_amount:full")],
        [InlineKeyboardButton(text="Boshqa summa kiritish", callback_data="cash_amount:custom")],
    ])
    await message.answer(
        f"👤 <b>O'quvchi:</b> {student.full_name} (ID: <code>{student_id}</code>)\n"
        f"👥 <b>Guruh:</b> {data['group_name']}\n\n"
        f"To'lov summasini tanlang:",
        reply_markup=keyboard,
    )


@router.callback_query(F.data == "cash_amount:full")
async def cash_payment_full_amount(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await _save_cash_payment(callback.from_user.id, data, data["course_price"])
    await callback.message.edit_text(
        f"✅ <b>To'lov muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"👤 O'quvchi: <b>{data['student_name']}</b>\n"
        f"👥 Guruh: <b>{data['group_name']}</b>\n"
        f"💰 Summa: <b>{data['course_price']:,.0f} so'm</b>\n\n"
        f"O'quvchi rasman guruhga qo'shildi va unga xabar yuborildi."
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
        f"✅ <b>To'lov muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"👤 O'quvchi: <b>{data['student_name']}</b>\n"
        f"👥 Guruh: <b>{data['group_name']}</b>\n"
        f"💰 Summa: <b>{amount:,.0f} so'm</b>\n\n"
        f"O'quvchi rasman guruhga qo'shildi va unga xabar yuborildi."
    )


async def _save_cash_payment(teacher_id: int, data: dict, amount: float):
    student_id = data["student_id"]
    group_id = data["group_id"]
    course_price = data.get("course_price", 0.0)

    async with async_session() as session:
        payment = Payment(
            student_id=student_id,
            group_id=group_id,
            amount=amount,
            method=PaymentMethodEnum.cash,
            status=PaymentStatusEnum.confirmed,
            confirmed_by=teacher_id,
            paid_at=datetime.utcnow(),
        )
        session.add(payment)

        # Enrollment yaratish
        result = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.group_id == group_id,
            )
        )
        existing_enrollment = result.scalar_one_or_none()
        if existing_enrollment is None:
            session.add(Enrollment(
                student_id=student_id,
                group_id=group_id,
                status=EnrollmentStatusEnum.active,
                enrolled_at=datetime.utcnow(),
            ))

        # Guruh & O'qituvchi
        group = await session.get(Group, group_id)
        teacher = await session.get(User, group.teacher_id) if group and group.teacher_id else None

        # TZ: 5% referal chegirma faqat to'liq to'lov to'langandagina beriladi!
        student = await session.get(User, student_id)
        referrer_id = None
        is_full_payment = amount >= course_price

        if is_full_payment and student and student.referred_by and not student.referral_bonus_given:
            session.add(ReferralBonus(
                user_id=student.referred_by,
                referred_student_id=student_id,
                bonus_percent=5.0,
                status="pending",
                is_used=False,
            ))
            student.referral_bonus_given = True
            referrer_id = student.referred_by

        await session.commit()

    # O'quvchiga tabrik
    from main import bot
    teacher_name = teacher.full_name if teacher else "O'qituvchi"
    schedule_str = _format_schedule(group.schedule if group else None, student.language.value if student and student.language else "uz")
    room_str = group.room or group.zoom_link or "O'quv markazi xonasi"

    congrats_text = (
        f"🎉 <b>To'lovingiz tasdiqlandi!</b>\n\n"
        f"Siz rasman guruhga qabul qilindingiz:\n"
        f"👥 <b>Guruh:</b> {group.name if group else ''}\n"
        f"👨‍🏫 <b>O'qituvchi:</b> {teacher_name}\n"
        f"🗓 <b>Dars jadvali:</b> {schedule_str}\n"
        f"🚪 <b>Xona / Manzil:</b> {room_str}\n\n"
        f"Endi bot menyusidan «📅 Jadvalim» va «📋 Uy Vazifam» bo'limlarini kuzatib borishingiz mumkin. Muvaffaqiyat tilaymiz! 🚀"
    )
    try:
        await bot.send_message(student_id, congrats_text, parse_mode="HTML")
    except Exception:
        pass

    if referrer_id:
        try:
            await award_badge_if_eligible(referrer_id, "ambassador")
            await bot.send_message(
                referrer_id,
                f"🎁 <b>Ajoyib xabar!</b>\n\n"
                f"Siz taklif qilgan do'stingiz (<b>{student.full_name}</b>) kurs to'lovini to'liq amalga oshirdi va o'qishni boshladi!\n"
                f"Sizga keyingi oy to'lovi uchun <b>+5% chegirma bonusi</b> va 👥 <b>Ambassador badge</b> berildi! 🌟",
            )
        except Exception:
            pass


@router.message(Command("refund"))
@router.message(F.text.in_(ALL_REFUND_BUTTONS))
async def start_refund(message: Message, state: FSMContext):
    if not await _is_teacher_or_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat o'qituvchilar va adminlar uchun.")
        return

    groups = await _get_teacher_groups(message.from_user.id)
    if not groups:
        await message.answer("Sizga biriktirilgan faol guruh topilmadi.")
        return

    await message.answer(
        "💰 <b>Qaytarish (Refund) hisob-kitobi</b>\n\nGuruhni tanlang:",
        reply_markup=_groups_keyboard(groups, "refund_group"),
    )


@router.callback_query(F.data.startswith("refund_group:"))
async def refund_group_selected(callback: CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        group = await session.get(Group, group_id)
        course = await session.get(Course, group.course_id)

        # Shu guruhdagi o'quvchilar
        enr_res = await session.execute(
            select(User)
            .join(Enrollment, Enrollment.student_id == User.id)
            .where(Enrollment.group_id == group_id)
        )
        students = enr_res.scalars().all()

        price_per_lesson = course.effective_price_per_lesson if course else 0.0

    await state.update_data(
        group_id=group_id,
        group_name=group.name,
        price_per_lesson=price_per_lesson,
    )

    buttons = [
        [InlineKeyboardButton(text=f"👤 {s.full_name}", callback_data=f"refund_student:{s.id}")]
        for s in students
    ]
    buttons.append([InlineKeyboardButton(text="⌨️ Telegram ID orqali", callback_data="refund_manual_id")])
    buttons.append([InlineKeyboardButton(text="◀️ Ortga", callback_data="refund_back_groups")])

    await callback.message.edit_text(
        f"👥 <b>Guruh:</b> {group.name}\n"
        f"💵 <b>Bir dars narxi:</b> {price_per_lesson:,.0f} so'm\n\n"
        f"Refund hisoblanadigan o'quvchini tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data == "refund_back_groups")
async def refund_back_groups(callback: CallbackQuery, state: FSMContext):
    groups = await _get_teacher_groups(callback.from_user.id)
    await callback.message.edit_text(
        "💰 <b>Qaytarish (Refund) hisob-kitobi</b>\n\nGuruhni tanlang:",
        reply_markup=_groups_keyboard(groups, "refund_group"),
    )
    await callback.answer()


@router.callback_query(F.data == "refund_manual_id")
async def refund_manual_id(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RefundRequest.entering_student_id)
    await callback.message.edit_text("O'quvchining Telegram ID raqamini kiriting:")
    await callback.answer()


@router.callback_query(F.data.startswith("refund_student:"))
async def refund_student_selected(callback: CallbackQuery, state: FSMContext):
    student_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    group_id = data["group_id"]

    async with async_session() as session:
        student = await session.get(User, student_id)
        group = await session.get(Group, group_id)
        course = await session.get(Course, group.course_id) if group else None

        # 1. To'langan summa: eng so'nggi to'lovlar
        result = await session.execute(
            select(Payment).where(
                Payment.student_id == student_id,
                Payment.group_id == group_id,
                Payment.status.in_([PaymentStatusEnum.confirmed, "confirmed"]),
            ).order_by(Payment.id.desc())
        )
        payments = result.scalars().all()
        total_paid = sum(float(p.amount) for p in payments)

        if total_paid <= 0:
            last_pay_res = await session.execute(
                select(Payment).where(
                    Payment.student_id == student_id,
                    Payment.status.in_([PaymentStatusEnum.confirmed, "confirmed"]),
                ).order_by(Payment.id.desc())
            )
            last_pay = last_pay_res.scalars().first()
            if last_pay:
                total_paid = float(last_pay.amount)
            elif course:
                total_paid = float(course.price)

        # 2. Qatnashgan darslar sonini attendance jadvalidan olish (TZ 9)
        att_res = await session.execute(
            select(func.count(Attendance.id)).where(
                Attendance.student_id == student_id,
                Attendance.group_id == group_id,
                Attendance.status.in_([AttendanceStatusEnum.present, AttendanceStatusEnum.late, "present", "late"]),
            )
        )
        lessons_attended = att_res.scalar() or 0

        # 3. Formula: refund_amount = total_paid - (price_per_lesson * lessons_attended)
        price_per_lesson = data.get("price_per_lesson") or (course.effective_price_per_lesson if course else 0.0)
        used_amount = min(price_per_lesson * lessons_attended, total_paid)
        refund_amount = max(total_paid - used_amount, 0.0)

        refund = Refund(
            student_id=student_id,
            group_id=group_id,
            reason=f"Avtomatik hisob: {lessons_attended} ta darsga qatnashgan",
            calculated_amount=refund_amount,
            status="pending",
        )
        session.add(refund)
        await session.flush()
        refund_id = refund.id
        await session.commit()

    await state.clear()

    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Refundni tasdiqlash", callback_data=f"approve_refund:{refund_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_refund:{refund_id}"),
    ]])

    await callback.message.edit_text(
        f"📋 <b>Qaytarish (Refund) hisob-kitobi (TZ 9 formula):</b>\n\n"
        f"👤 <b>O'quvchi:</b> {student.full_name}\n"
        f"👥 <b>Guruh:</b> {data['group_name']}\n"
        f"💵 <b>Jami to'langan:</b> {total_paid:,.0f} so'm\n"
        f"📊 <b>Qatnashgan darslar:</b> {lessons_attended} ta x {price_per_lesson:,.0f} = {used_amount:,.0f} so'm\n\n"
        f"💰 <b>Qaytariladigan summa:</b> <b>{refund_amount:,.0f} so'm</b>\n\n"
        f"Status: ⏳ Kutilmoqda (Admin tasdiqlashi uchun yuborildi)",
        reply_markup=confirm_keyboard,
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
        await message.answer("Bunday ID bilan foydalanuvchi topilmadi. Qaytadan kiriting:")
        return

    data = await state.get_data()
    group_id = data["group_id"]

    async with async_session() as session:
        group = await session.get(Group, group_id)
        course = await session.get(Course, group.course_id) if group else None

        result = await session.execute(
            select(Payment).where(
                Payment.student_id == student_id,
                Payment.group_id == group_id,
                Payment.status.in_([PaymentStatusEnum.confirmed, "confirmed"]),
            ).order_by(Payment.id.desc())
        )
        payments = result.scalars().all()
        total_paid = sum(float(p.amount) for p in payments)

        if total_paid <= 0:
            last_pay_res = await session.execute(
                select(Payment).where(
                    Payment.student_id == student_id,
                    Payment.status.in_([PaymentStatusEnum.confirmed, "confirmed"]),
                ).order_by(Payment.id.desc())
            )
            last_pay = last_pay_res.scalars().first()
            if last_pay:
                total_paid = float(last_pay.amount)
            elif course:
                total_paid = float(course.price)

        att_res = await session.execute(
            select(func.count(Attendance.id)).where(
                Attendance.student_id == student_id,
                Attendance.group_id == group_id,
                Attendance.status.in_([AttendanceStatusEnum.present, AttendanceStatusEnum.late, "present", "late"]),
            )
        )
        lessons_attended = att_res.scalar() or 0

        price_per_lesson = data.get("price_per_lesson") or (course.effective_price_per_lesson if course else 0.0)
        used_amount = min(price_per_lesson * lessons_attended, total_paid)
        refund_amount = max(total_paid - used_amount, 0.0)

        refund = Refund(
            student_id=student_id,
            group_id=group_id,
            reason=f"Avtomatik hisob: {lessons_attended} ta darsga qatnashgan",
            calculated_amount=refund_amount,
            status="pending",
        )
        session.add(refund)
        await session.flush()
        refund_id = refund.id
        await session.commit()

    await state.clear()

    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Refundni tasdiqlash", callback_data=f"approve_refund:{refund_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_refund:{refund_id}"),
    ]])

    await message.answer(
        f"📋 <b>Qaytarish (Refund) hisob-kitobi (TZ 9 formula):</b>\n\n"
        f"👤 <b>O'quvchi:</b> {student.full_name}\n"
        f"👥 <b>Guruh:</b> {data['group_name']}\n"
        f"💵 <b>Jami to'langan:</b> {total_paid:,.0f} so'm\n"
        f"📊 <b>Qatnashgan darslar:</b> {lessons_attended} ta x {price_per_lesson:,.0f} = {used_amount:,.0f} so'm\n\n"
        f"💰 <b>Qaytariladigan summa:</b> <b>{refund_amount:,.0f} so'm</b>\n\n"
        f"Status: ⏳ Kutilmoqda (Admin tasdiqlashi uchun yuborildi)",
        reply_markup=confirm_keyboard,
    )


@router.callback_query(F.data.startswith("approve_refund:"))
async def approve_refund(callback: CallbackQuery):
    if not await _is_teacher_or_admin(callback.from_user.id):
        await callback.answer("Faqat admin tasdiqlay oladi.", show_alert=True)
        return

    refund_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        result = await session.execute(
            update(Refund)
            .where(Refund.id == refund_id, Refund.status == "pending")
            .values(
                status="approved",
                approved_by=callback.from_user.id,
                processed_at=datetime.utcnow(),
            )
        )
        if result.rowcount == 0:
            await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
            return

        refund = await session.get(Refund, refund_id)

        # 1. O'quvchini guruhdan chiqaramiz (Enrollment deactive qilamiz)
        enr_res = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == refund.student_id,
                Enrollment.group_id == refund.group_id,
                Enrollment.is_active == True,
            )
        )
        enr = enr_res.scalar_one_or_none()
        if enr:
            enr.status = EnrollmentStatusEnum.dropped
            enr.is_active = False
            enr.completed_at = datetime.utcnow()

        # 2. To'lov holatini refunded ga o'tkazamiz
        if refund.payment_id:
            pay = await session.get(Payment, refund.payment_id)
            if pay:
                pay.status = PaymentStatusEnum.refunded
        else:
            await session.execute(
                update(Payment)
                .where(
                    Payment.student_id == refund.student_id,
                    Payment.group_id == refund.group_id,
                    Payment.status == PaymentStatusEnum.confirmed,
                )
                .values(status=PaymentStatusEnum.refunded)
            )

        group = await session.get(Group, refund.group_id)
        group_name = group.name if group else "Guruh"

        await session.commit()

    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ <b>Refund tasdiqlandi va o'quvchi guruhdan chiqarildi!</b> (Admin: {callback.from_user.full_name})"
    )
    await callback.answer("Refund tasdiqlandi!")

    from main import bot
    try:
        await bot.send_message(
            refund.student_id,
            f"💰 <b>Qaytarish (Refund) so'rovingiz tasdiqlandi!</b>\n\n"
            f"👥 Guruh: <b>{group_name}</b>\n"
            f"💵 Qaytariladigan summa: <b>{float(refund.calculated_amount):,.0f} so'm</b>\n\n"
            f"ℹ️ <i>Siz rasman guruh a'zoligidan chiqarildingiz. Mablag'ni qabul qilish uchun ma'muriyat bilan bog'laning.</i>",
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("reject_refund:"))
async def reject_refund(callback: CallbackQuery):
    if not await _is_teacher_or_admin(callback.from_user.id):
        await callback.answer("Faqat admin rad eta oladi.", show_alert=True)
        return

    refund_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        result = await session.execute(
            update(Refund)
            .where(Refund.id == refund_id, Refund.status == "pending")
            .values(
                status="rejected",
                approved_by=callback.from_user.id,
                processed_at=datetime.utcnow(),
            )
        )
        await session.commit()

        if result.rowcount == 0:
            await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
            return

        refund = await session.get(Refund, refund_id)

    await callback.message.edit_text(
        callback.message.text + f"\n\n❌ <b>Refund rad etildi!</b> (Admin: {callback.from_user.full_name})"
    )
    await callback.answer("Refund rad etildi.")