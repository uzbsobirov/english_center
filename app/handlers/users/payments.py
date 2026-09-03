"""
O'quvchi tomonidan to'lov so'rovi yuborish (TZ v2.6, 7.2, 9, 14.1).
Oqim:
1. O'quvchi guruh tanlaydi
2. Referal chegirmalari hisoblanadi (+5% har bir taklif qilingan do'st uchun)
3. To'lov usuli tanlanadi (💵 Naqd / 🌐 Online: Payme, Click, Uzum)
4. Naqd: O'qituvchiga/adminlarga atomik tasdiqlash tugmali xabar boradi
5. Tasdiqlangach: Payment confirmed -> Enrollment yaratiladi -> Referrerga bonus -> O'quvchiga tabrik
"""
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_i18n import I18nContext
from sqlalchemy import select, update

from backend.database import async_session
from backend.models import (
    Group, Course, Payment, PaymentMethodEnum, PaymentStatusEnum,
    Enrollment, EnrollmentStatusEnum, User, ReferralBonus,
    FreeTrialRequest, TestResult, Test
)
from backend.services.gamification import award_badge_if_eligible

from backend.utils.formatters import format_schedule

router = Router()

_format_schedule = format_schedule

PAY_BUTTON_TEXTS = {
    "💳 To'lov", "💳 Оплата", "💳 Payment",
    "💳 To'lov qilish", "💳 Оплатить", "💳 Make payment",
    "To'lov", "Оплата", "Payment",
}


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
@router.callback_query(F.data == "start_payment_flow")
async def start_payment(event: Message | CallbackQuery, i18n: I18nContext, state: FSMContext):
    lang = getattr(i18n, "locale", "uz") or "uz"
    student_id = event.from_user.id
    msg_target = event if isinstance(event, Message) else event.message

    async with async_session() as session:
        # 1. O'quvchining faol a'zo bo'lgan guruhi bormi?
        enrolled_res = await session.execute(
            select(Group, Course)
            .join(Course, Group.course_id == Course.id)
            .join(Enrollment, Group.id == Enrollment.group_id)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.is_active == True,
                Group.is_active == True,
            ).order_by(Enrollment.enrolled_at.desc()).limit(1)
        )
        matched = enrolled_res.first()

        # 2. Free darsga yozilgan/taklif qilingan guruhi bormi?
        if not matched:
            trial_res = await session.execute(
                select(FreeTrialRequest)
                .where(FreeTrialRequest.student_id == student_id)
                .order_by(FreeTrialRequest.created_at.desc()).limit(1)
            )
            trial = trial_res.scalars().first()
            if trial:
                if trial.group_id:
                    grp = await session.get(Group, trial.group_id)
                    if grp and grp.is_active:
                        crs = await session.get(Course, grp.course_id)
                        if crs:
                            matched = (grp, crs)
                elif trial.test_result_id:
                    t_res = await session.get(TestResult, trial.test_result_id)
                    if t_res:
                        t_obj = await session.get(Test, t_res.test_id)
                        if t_obj:
                            grp_res = await session.execute(
                                select(Group, Course)
                                .join(Course, Group.course_id == Course.id)
                                .where(
                                    Course.level == t_obj.level,
                                    Group.is_active == True,
                                ).limit(1)
                            )
                            matched = grp_res.first()

        if matched:
            group, course = matched
            teacher = await session.get(User, group.teacher_id) if group.teacher_id else None
            teacher_name = teacher.full_name if teacher else "O'qituvchi"
            sched_str = _format_schedule(group.schedule, lang)
            course_title = course.title.get(lang, course.title.get("uz", "Kurs")) if isinstance(course.title, dict) else str(course.title)

            buttons = [
                [InlineKeyboardButton(
                    text=f"💳 {group.name} uchun to'lov qilish",
                    callback_data=f"pay_group:{group.id}",
                )],
                [InlineKeyboardButton(
                    text="🔄 Boshqa guruhni tanlash",
                    callback_data="pay_show_all_groups",
                )],
            ]

            card_text = (
                f"💳 <b>Kurs To'lovi</b>\n\n"
                f"🎯 <b>Siz yozilgan guruh:</b> <b>{group.name}</b>\n"
                f"📚 <b>Kurs:</b> {course_title} ({course.level.value})\n"
                f"👨‍🏫 <b>O'qituvchi:</b> {teacher_name}\n"
                f"🗓 <b>Dars jadvali:</b> {sched_str}\n"
                f"💰 <b>Oylik to'lov:</b> <b>{float(course.price):,.0f} so'm</b>\n\n"
                f"<i>To'lovni amalga oshirish uchun quyidagi tugmani bosing:</i>"
            )
            if isinstance(event, CallbackQuery):
                try:
                    await event.message.edit_text(card_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
                except Exception:
                    try:
                        await event.message.delete()
                    except Exception:
                        pass
                    await event.message.answer(card_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
                await event.answer()
            else:
                await event.answer(card_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
            return

    # Agar aniq biriktirilgan guruh topilmasa — barcha faol guruhlarni ko'rsatamiz
    await _show_all_groups_menu(event, lang)


async def _show_all_groups_menu(target: Message | CallbackQuery, lang: str):
    groups = await _get_active_groups()
    if not groups:
        msg = (
            "Hozircha faol guruhlar mavjud emas."
            if lang == "uz"
            else ("В настоящее время активных групп нет." if lang == "ru" else "No active groups available at the moment.")
        )
        if isinstance(target, CallbackQuery):
            await target.message.edit_text(msg)
            await target.answer()
        else:
            await target.answer(msg)
        return

    buttons = [
        [InlineKeyboardButton(
            text=f"👥 {group.name} ({float(course.price):,.0f} so'm)",
            callback_data=f"pay_group:{group.id}",
        )]
        for group, course in groups
    ]

    header_text = (
        "💳 <b>Kurs to'lovi</b>\n\nTo'lov qilmoqchi bo'lgan guruhingizni tanlang:"
        if lang == "uz"
        else (
            "💳 <b>Оплата курса</b>\n\nВыберите группу, за которую хотите оплатить:"
            if lang == "ru"
            else "💳 <b>Course Payment</b>\n\nPlease select the group you want to pay for:"
        )
    )
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(header_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        await target.answer()
    else:
        await target.answer(header_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data == "pay_show_all_groups")
async def pay_show_all_groups_callback(callback: CallbackQuery, i18n: I18nContext):
    lang = getattr(i18n, "locale", "uz") or "uz"
    await _show_all_groups_menu(callback, lang)


@router.callback_query(F.data.startswith("pay_group:"))
async def payment_group_selected(callback: CallbackQuery, i18n: I18nContext, state: FSMContext):
    lang = getattr(i18n, "locale", "uz") or "uz"
    group_id = int(callback.data.split(":")[1])
    student_id = callback.from_user.id

    async with async_session() as session:
        group = await session.get(Group, group_id)
        if not group:
            await callback.answer("Guruh topilmadi", show_alert=True)
            return
        course = await session.get(Course, group.course_id)
        if not course:
            await callback.answer("Kurs topilmadi", show_alert=True)
            return

        # Referal chegirmalarini tekshirish (TZ 14.1)
        bonus_res = await session.execute(
            select(ReferralBonus).where(
                ReferralBonus.user_id == student_id,
                ReferralBonus.status == "pending",
                ReferralBonus.is_used == False,
            )
        )
        bonuses = bonus_res.scalars().all()
        total_discount_pct = sum(float(b.bonus_percent) for b in bonuses)
        total_discount_pct = min(total_discount_pct, 100.0)

    base_price = float(course.price)
    discount_amount = base_price * (total_discount_pct / 100.0)
    final_price = max(base_price - discount_amount, 0.0)

    # State ga saqlash
    await state.update_data(
        group_id=group_id,
        group_name=group.name,
        base_price=base_price,
        discount_amount=discount_amount,
        final_price=final_price,
        discount_pct=total_discount_pct,
    )

    if lang == "uz":
        text = (
            f"📚 <b>Guruh:</b> {group.name}\n"
            f"💵 <b>Asl narx:</b> {base_price:,.0f} so'm\n"
        )
        if total_discount_pct > 0:
            text += f"🎁 <b>Referal chegirma:</b> -{total_discount_pct:.0f}% (-{discount_amount:,.0f} so'm)\n"
        text += f"💰 <b>To'lanadigan summa:</b> {final_price:,.0f} so'm\n\nTo'lov usulini tanlang:"
        cash_btn = "💵 Naqd to'lov (Ofisda / O'qituvchiga)"
        online_btn = "🌐 Online to'lov (Payme / Click / Uzum)"
        back_btn = "◀️ Boshqa guruh tanlash"
    elif lang == "ru":
        text = (
            f"📚 <b>Группа:</b> {group.name}\n"
            f"💵 <b>Исходная цена:</b> {base_price:,.0f} сум\n"
        )
        if total_discount_pct > 0:
            text += f"🎁 <b>Реферальная скидка:</b> -{total_discount_pct:.0f}% (-{discount_amount:,.0f} сум)\n"
        text += f"💰 <b>Итого к оплате:</b> {final_price:,.0f} сум\n\nВыберите способ оплаты:"
        cash_btn = "💵 Наличными (В офисе / Учителю)"
        online_btn = "🌐 Онлайн оплата (Payme / Click / Uzum)"
        back_btn = "◀️ Выбрать другую группу"
    else:
        text = (
            f"📚 <b>Group:</b> {group.name}\n"
            f"💵 <b>Standard price:</b> {base_price:,.0f} UZS\n"
        )
        if total_discount_pct > 0:
            text += f"🎁 <b>Referral discount:</b> -{total_discount_pct:.0f}% (-{discount_amount:,.0f} UZS)\n"
        text += f"💰 <b>Total payable:</b> {final_price:,.0f} UZS\n\nChoose payment method:"
        cash_btn = "💵 Cash (At Office / To Teacher)"
        online_btn = "🌐 Online Payment (Payme / Click / Uzum)"
        back_btn = "◀️ Select another group"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=cash_btn, callback_data=f"pay_method:cash:{group_id}")],
        [InlineKeyboardButton(text=online_btn, callback_data=f"pay_method:online:{group_id}")],
        [InlineKeyboardButton(text=back_btn, callback_data="pay_back_groups")],
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "pay_back_groups")
async def pay_back_to_groups(callback: CallbackQuery, i18n: I18nContext, state: FSMContext):
    await start_payment(callback.message, i18n, state)
    await callback.answer()


@router.callback_query(F.data.startswith("pay_method:online:"))
async def payment_online_selected(callback: CallbackQuery, i18n: I18nContext, state: FSMContext):
    lang = getattr(i18n, "locale", "uz") or "uz"
    group_id = int(callback.data.split(":")[2])
    data = await state.get_data()
    final_price = data.get("final_price", 0.0)
    group_name = data.get("group_name", "Guruh")

    if lang == "uz":
        text = (
            f"🌐 <b>Online To'lov (Payme / Click / Uzum)</b>\n\n"
            f"👥 Guruh: <b>{group_name}</b>\n"
            f"💰 To'lov summasi: <b>{final_price:,.0f} so'm</b>\n\n"
            f"To'lov tizimini tanlang:"
        )
    elif lang == "ru":
        text = (
            f"🌐 <b>Онлайн Оплата (Payme / Click / Uzum)</b>\n\n"
            f"👥 Группа: <b>{group_name}</b>\n"
            f"💰 Сумма к оплате: <b>{final_price:,.0f} сум</b>\n\n"
            f"Выберите платежную систему:"
        )
    else:
        text = (
            f"🌐 <b>Online Payment (Payme / Click / Uzum)</b>\n\n"
            f"👥 Group: <b>{group_name}</b>\n"
            f"💰 Payable amount: <b>{final_price:,.0f} UZS</b>\n\n"
            f"Choose payment provider:"
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💳 Payme", callback_data=f"online_pay_demo:payme:{group_id}"),
            InlineKeyboardButton(text="💳 Click", callback_data=f"online_pay_demo:click:{group_id}"),
        ],
        [
            InlineKeyboardButton(text="🟣 Uzum Bank", callback_data=f"online_pay_demo:uzum:{group_id}"),
        ],
        [
            InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"pay_group:{group_id}"),
        ],
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("online_pay_demo:"))
async def online_pay_demo_process(callback: CallbackQuery, i18n: I18nContext, state: FSMContext):
    parts = callback.data.split(":")
    provider = parts[1]
    group_id = int(parts[2])
    data = await state.get_data()
    final_price = data.get("final_price", 0.0)

    # TZ 9: Online to'lov demo invoys/simulyatsiya
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ To'lovni tasdiqlash (Demo)", callback_data=f"online_pay_complete:{provider}:{group_id}")],
        [InlineKeyboardButton(text="◀️ Bekor qilish", callback_data=f"pay_group:{group_id}")],
    ])

    await callback.message.edit_text(
        f"🔗 <b>{provider.upper()} To'lov Sahifasi</b>\n\n"
        f"💳 Invoys: <code>INV-{callback.from_user.id}-{group_id}</code>\n"
        f"💰 Summa: <b>{final_price:,.0f} so'm</b>\n\n"
        f"Hozirda sinov rejimida to'lovni tasdiqlashingiz mumkin:",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("online_pay_complete:"))
async def online_pay_complete(callback: CallbackQuery, i18n: I18nContext, state: FSMContext):
    parts = callback.data.split(":")
    provider = parts[1]
    group_id = int(parts[2])
    student_id = callback.from_user.id
    data = await state.get_data()
    final_price = data.get("final_price", 0.0)
    discount_amount = data.get("discount_amount", 0.0)

    method_map = {
        "payme": PaymentMethodEnum.payme,
        "click": PaymentMethodEnum.click,
        "uzum": PaymentMethodEnum.uzum,
    }
    method_enum = method_map.get(provider, PaymentMethodEnum.click)

    async with async_session() as session:
        group = await session.get(Group, group_id)
        payment = Payment(
            student_id=student_id,
            group_id=group_id,
            amount=final_price,
            discount_amount=discount_amount,
            method=method_enum,
            status=PaymentStatusEnum.confirmed,
            external_transaction_id=f"TX-{provider.upper()}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            paid_at=datetime.utcnow(),
        )
        session.add(payment)

        # Enrollment tekshirish va yaratish
        enr_res = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.group_id == group_id,
            )
        )
        if enr_res.scalar_one_or_none() is None:
            session.add(Enrollment(
                student_id=student_id,
                group_id=group_id,
                status=EnrollmentStatusEnum.active,
                enrolled_at=datetime.utcnow(),
            ))

        # O'quvchining ishlatilgan referal bonuslarini yopish
        if discount_amount > 0:
            await session.execute(
                update(ReferralBonus)
                .where(
                    ReferralBonus.user_id == student_id,
                    ReferralBonus.status == "pending",
                    ReferralBonus.is_used == False,
                )
                .values(is_used=True, status="applied", applied_at=datetime.utcnow())
            )

        # Agar bu o'quvchini birov taklif qilgan bo'lsa va to'lov to'liq kurs narxi bo'lsa (TZ 14):
        student = await session.get(User, student_id)
        course = await session.get(Course, group.course_id) if group else None
        course_price = float(course.price) if course else 0.0
        is_full_payment = (final_price + discount_amount) >= course_price

        referrer_id = None
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

        group_name = group.name if group else "Guruh"
        group_chat_link = group.group_chat_link if group else None
        student_name = student.full_name if student else (callback.from_user.full_name or "O'quvchi")

        await session.commit()

    # Guruh linki tugmasi
    success_buttons = []
    if group_chat_link:
        success_buttons.append([InlineKeyboardButton(text="👥 Guruh Telegram Chati", url=group_chat_link)])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=success_buttons) if success_buttons else None

    chat_link_info = f"🔗 <b>Guruh Telegram Chati:</b> <a href='{group_chat_link}'>Guruhga qo'shilish</a>\n\n" if group_chat_link else ""

    await callback.message.edit_text(
        f"🎉 <b>To'lovingiz muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"👥 Guruh: <b>{group_name}</b>\n"
        f"💳 To'lov turi: <b>{provider.upper()}</b>\n"
        f"💰 To'langan summa: <b>{final_price:,.0f} so'm</b>\n\n"
        f"{chat_link_info}"
        f"Siz rasman guruh a'zosiga aylandingiz! Endi «📅 Jadvalim» va «📋 Uy Vazifam» bo'limlaridan to'liq foydalanishingiz mumkin.",
        reply_markup=reply_markup,
    )
    await callback.answer("To'lov muvaffaqiyatli!", show_alert=True)
    await state.clear()

    # Referrer ga xabar yuborish
    if referrer_id:
        from main import bot
        try:
            await award_badge_if_eligible(referrer_id, "ambassador")
            await bot.send_message(
                referrer_id,
                f"🎁 <b>Ajoyib xabar!</b>\n\n"
                f"Siz taklif qilgan do'stingiz (<b>{student_name}</b>) kurs to'lovini amalga oshirdi va o'qishni boshladi!\n"
                f"Sizga keyingi oy to'lovi uchun <b>+5% chegirma bonusi</b> va 👥 <b>Ambassador badge</b> berildi! 🌟",
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("pay_method:cash:"))
async def payment_cash_requested(callback: CallbackQuery, i18n: I18nContext, state: FSMContext):
    lang = getattr(i18n, "locale", "uz") or "uz"
    group_id = int(callback.data.split(":")[2])
    student_id = callback.from_user.id
    student_name = callback.from_user.full_name or "O'quvchi"
    username_str = f" (@{callback.from_user.username})" if callback.from_user.username else ""

    data = await state.get_data()
    final_price = data.get("final_price", 0.0)
    discount_amount = data.get("discount_amount", 0.0)

    async with async_session() as session:
        group = await session.get(Group, group_id)
        if not group:
            await callback.answer("Guruh topilmadi", show_alert=True)
            return
        course = await session.get(Course, group.course_id)

        payment = Payment(
            student_id=student_id,
            group_id=group_id,
            amount=final_price or course.price,
            discount_amount=discount_amount,
            method=PaymentMethodEnum.cash,
            status=PaymentStatusEnum.pending,
        )
        session.add(payment)
        await session.flush()
        payment_id = payment.id
        await session.commit()

        teacher = await session.get(User, group.teacher_id) if group.teacher_id else None

    if lang == "uz":
        student_msg = (
            f"✅ <b>Naqd to'lov so'rovingiz yuborildi!</b>\n\n"
            f"👥 Guruh: <b>{group.name}</b>\n"
            f"💰 Summa: <b>{final_price:,.0f} so'm</b>\n\n"
            f"💵 Iltimos, naqd pulni ofisimizga yoki o'qituvchingizga topshiring. "
            f"Pul qabul qilib olingach, o'qituvchi/admin to'lovingizni tasdiqlaydi."
        )
    elif lang == "ru":
        student_msg = (
            f"✅ <b>Запрос на оплату наличными отправлен!</b>\n\n"
            f"👥 Группа: <b>{group.name}</b>\n"
            f"💰 Сумма: <b>{final_price:,.0f} сум</b>\n\n"
            f"💵 Пожалуйста, передайте наличные в наш офис или преподавателю. "
            f"После получения оплаты преподаватель/администратор подтвердит её."
        )
    else:
        student_msg = (
            f"✅ <b>Cash payment request sent!</b>\n\n"
            f"👥 Group: <b>{group.name}</b>\n"
            f"💰 Amount: <b>{final_price:,.0f} UZS</b>\n\n"
            f"💵 Please hand over the cash to our office or your teacher. "
            f"Once received, the teacher/admin will confirm your payment."
        )

    await callback.message.edit_text(student_msg)
    await callback.answer()

    # O'qituvchi va Adminlarga interaktiv tasdiqlash xabari
    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_payment:{payment_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_payment:{payment_id}"),
    ]])
    admin_text = (
        f"💵 <b>Yangi naqd to'lov so'rovi!</b>\n\n"
        f"👤 O'quvchi: <a href='tg://user?id={student_id}'>{student_name}</a>{username_str}\n"
        f"👥 Guruh: <b>{group.name}</b>\n"
        f"💰 To'lanadigan summa: <b>{final_price:,.0f} so'm</b>\n"
        f"🎁 Chegirma: <b>{discount_amount:,.0f} so'm</b>\n\n"
        f"Pulni qabul qilib olgach, quyidagi tugma orqali tasdiqlang:"
    )

    from main import bot
    from backend.services.user_service import get_admin_ids

    recipients = [group.teacher_id] if teacher is not None else []
    admin_ids = await get_admin_ids()
    for aid in admin_ids:
        if aid not in recipients:
            recipients.append(aid)

    for recipient_id in recipients:
        try:
            await bot.send_message(recipient_id, admin_text, reply_markup=confirm_keyboard, parse_mode="HTML")
        except Exception:
            continue


@router.callback_query(F.data.startswith("confirm_payment:"))
async def confirm_payment(callback: CallbackQuery):
    payment_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        # Atomik update (TZ 7.2 & 18.2)
        result = await session.execute(
            update(Payment)
            .where(Payment.id == payment_id, Payment.status == PaymentStatusEnum.pending)
            .values(
                status=PaymentStatusEnum.confirmed,
                confirmed_by=callback.from_user.id,
                paid_at=datetime.utcnow(),
            )
        )
        await session.commit()

        if result.rowcount == 0:
            await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
            return

        payment = await session.get(Payment, payment_id)
        group = await session.get(Group, payment.group_id)
        teacher = await session.get(User, group.teacher_id) if group and group.teacher_id else None

        # Enrollment yaratish
        existing = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == payment.student_id,
                Enrollment.group_id == payment.group_id,
            )
        )
        if existing.scalar_one_or_none() is None:
            session.add(Enrollment(
                student_id=payment.student_id,
                group_id=payment.group_id,
                status=EnrollmentStatusEnum.active,
                enrolled_at=datetime.utcnow(),
            ))

        # Referal bonuslarni yopish
        if payment.discount_amount and payment.discount_amount > 0:
            await session.execute(
                update(ReferralBonus)
                .where(
                    ReferralBonus.user_id == payment.student_id,
                    ReferralBonus.status == "pending",
                    ReferralBonus.is_used == False,
                )
                .values(is_used=True, status="applied", applied_at=datetime.utcnow())
            )

        # Referrer ga bonus berish (faqat to'liq to'lov bo'lgandagina)
        student = await session.get(User, payment.student_id)
        course = await session.get(Course, group.course_id) if group else None
        course_price = float(course.price) if course else 0.0
        is_full_payment = (float(payment.amount) + float(payment.discount_amount or 0.0)) >= course_price

        referrer_id = None
        if is_full_payment and student and student.referred_by and not student.referral_bonus_given:
            session.add(ReferralBonus(
                user_id=student.referred_by,
                referred_student_id=student.id,
                bonus_percent=5.0,
                status="pending",
                is_used=False,
            ))
            student.referral_bonus_given = True
            referrer_id = student.referred_by
        teacher_name = teacher.full_name if teacher else "O'qituvchi tayinlanmoqda"
        student_lang = student.language.value if student and student.language else "uz"
        schedule_str = _format_schedule(group.schedule if group else None, student_lang)
        room_str = group.room or group.zoom_link or "O'quv markazi xonasi"
        group_name = group.name if group else ""
        group_chat_link = group.group_chat_link if group else None
        student_name = student.full_name if student else "O'quvchi"
        student_id_target = payment.student_id

        await session.commit()

    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ <b>Tasdiqlandi!</b> (Tasdiqladi: {callback.from_user.full_name})"
    )
    await callback.answer("To'lov tasdiqlandi!")

    # O'quvchiga tabrik va guruh ma'lumotlari
    from main import bot
    chat_link_info = f"🔗 <b>Guruh Telegram Chati:</b> <a href='{group_chat_link}'>Guruhga qo'shilish</a>\n\n" if group_chat_link else ""
    success_buttons = []
    if group_chat_link:
        success_buttons.append([InlineKeyboardButton(text="👥 Guruh Telegram Chati", url=group_chat_link)])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=success_buttons) if success_buttons else None

    congrats_text = (
        f"🎉 <b>To'lovingiz tasdiqlandi!</b>\n\n"
        f"Siz rasman guruhga qabul qilindingiz:\n"
        f"👥 <b>Guruh:</b> {group_name}\n"
        f"👨‍🏫 <b>O'qituvchi:</b> {teacher_name}\n"
        f"🗓 <b>Dars jadvali:</b> {schedule_str}\n"
        f"🚪 <b>Xona / Manzil:</b> {room_str}\n\n"
        f"{chat_link_info}"
        f"Endi bot menyusidan «📅 Jadvalim» va «📋 Uy Vazifam» bo'limlarini kuzatib borishingiz mumkin. O'qishlaringizda muvaffaqiyat tilaymiz! 🚀"
    )
    try:
        await bot.send_message(student_id_target, congrats_text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception:
        pass

    # Referrer ga xabarnoma
    if referrer_id:
        try:
            await award_badge_if_eligible(referrer_id, "ambassador")
            await bot.send_message(
                referrer_id,
                f"🎁 <b>Ajoyib xabar!</b>\n\n"
                f"Siz taklif qilgan do'stingiz (<b>{student_name}</b>) kurs to'lovini amalga oshirdi va o'qishni boshladi!\n"
                f"Sizga keyingi oy to'lovi uchun <b>+5% chegirma bonusi</b> va 👥 <b>Ambassador badge</b> berildi! 🌟",
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

    await callback.message.edit_text(
        callback.message.text + f"\n\n❌ <b>Rad etildi!</b> (Rad etdi: {callback.from_user.full_name})"
    )
    await callback.answer("Rad etildi.")

    from main import bot
    try:
        await bot.send_message(
            payment.student_id,
            "❌ Afsuski, to'lov so'rovingiz rad etildi. Iltimos, o'quv markazi ma'muriyati yoki o'qituvchingiz bilan bog'laning.",
        )
    except Exception:
        pass