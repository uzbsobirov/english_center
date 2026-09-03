"""
⚙️ Sozlamalar, Til, Telefon va Guruh o'zgartirish / Refund bo'limi (TZ v2.6, 3, 6.3, 7.6, 9.3-bo'limlar).
- Tilni o'zgartirish (🇺🇿 uz / 🇷🇺 ru / 🇬🇧 en)
- Telefon raqamini yangilash
- Guruhni o'zgartirish so'rovi (o'qituvchi / admin tasdiqlaydi)
- Qaytarish (Refund) so'rovi (formula bo'yicha avtomatik hisoblash)
"""
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram_i18n import I18nContext
from sqlalchemy import select, update

from backend.database import async_session
from backend.models import (
    User, LanguageEnum, Enrollment, Group, Course, Attendance,
    AttendanceStatusEnum, Payment, PaymentStatusEnum, Refund, GroupChangeRequest
)
from backend.services.user_service import get_admin_ids
from app.keyboards.main_menu import main_menu_keyboard

router = Router()


class SettingsFSM(StatesGroup):
    waiting_for_phone = State()
    choosing_new_group = State()
    group_change_reason = State()
    refund_reason = State()


SETTINGS_BUTTON_TEXTS = {
    "⚙️ Sozlamalar", "⚙️ Настройки", "⚙️ Settings",
    "🌐 Til", "🌐 Язык", "🌐 Language",
    "Sozlamalar", "Настройки", "Settings",
}


@router.message(Command("settings"))
@router.message(F.text.in_(SETTINGS_BUTTON_TEXTS))
async def show_settings(message: Message, i18n: I18nContext):
    user_id = message.from_user.id
    lang = getattr(i18n, "locale", "uz") or "uz"

    async with async_session() as session:
        user = await session.get(User, user_id)
        enr_res = await session.execute(
            select(Enrollment, Group, Course)
            .join(Group, Enrollment.group_id == Group.id)
            .join(Course, Group.course_id == Course.id)
            .where(Enrollment.student_id == user_id, Enrollment.is_active == True)
        )
        enr_row = enr_res.first()

    group_name = enr_row[1].name if enr_row else "Guruhsiz"
    phone_display = (user.phone if user and user.phone else "Kiritilmagan")

    lang_labels = {"uz": "🇺🇿 O'zbekcha", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}
    current_lang_label = lang_labels.get(lang, "🇺🇿 O'zbekcha")

    text = (
        f"⚙️ <b>Sozlamalar va Boshqaruv</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {message.from_user.full_name}\n"
        f"📱 <b>Telefon:</b> <code>{phone_display}</code>\n"
        f"🌐 <b>Joriy til:</b> {current_lang_label}\n"
        f"👥 <b>Faol guruh:</b> {group_name}\n\n"
        f"Quyidagi amallardan birini tanlang:"
    )

    buttons = [
        [
            InlineKeyboardButton(text="🌐 Tilni o'zgartirish", callback_data="settings:lang"),
            InlineKeyboardButton(text="📱 Telefonni yangilash", callback_data="settings:phone"),
        ]
    ]

    if enr_row:
        buttons.append([
            InlineKeyboardButton(text="👥 Guruhni o'zgartirish", callback_data="settings:change_group"),
            InlineKeyboardButton(text="💰 Qaytarish (Refund)", callback_data="settings:refund"),
        ])

    buttons.append([
        InlineKeyboardButton(text="◀️ Asosiy menyu", callback_data="settings:close")
    ])

    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data == "settings:lang")
async def settings_language_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbek tili", callback_data="switch_lang:uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский язык", callback_data="switch_lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="switch_lang:en")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="settings:back_to_menu")],
    ])
    await callback.message.edit_text("🌐 Tilni tanlang / Выберите язык / Choose language:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "settings:phone")
async def settings_update_phone(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsFSM.waiting_for_phone)
    cancel_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="◀️ Bekor qilish")],
        ],
        resize_keyboard=True,
    )
    await callback.message.delete()
    await callback.message.answer(
        "📱 <b>Yangi telefon raqamingizni yuboring:</b>\n"
        "Quyidagi «📱 Raqamni yuborish» tugmasini bosing yoki raqamni matn ko'rinishida yozing (masalan: <code>+998901234567</code>):",
        reply_markup=cancel_kb,
    )
    await callback.answer()


@router.message(SettingsFSM.waiting_for_phone, F.contact)
@router.message(SettingsFSM.waiting_for_phone, F.text)
async def process_phone_update(message: Message, state: FSMContext, i18n: I18nContext):
    if message.text in ("◀️ Bekor qilish", "◀️ Отмена", "◀️ Cancel"):
        await state.clear()
        await message.answer(
            "Bekor qilindi.",
            reply_markup=main_menu_keyboard(
                i18n,
                user_id=message.from_user.id,
                user_name=message.from_user.full_name,
                username=message.from_user.username,
            ),
        )
        return

    new_phone = None
    if message.contact:
        is_forwarded = bool(
            getattr(message, "forward_origin", None)
            or getattr(message, "forward_from", None)
            or getattr(message, "forward_from_chat", None)
        )
        if is_forwarded or message.contact.user_id != message.from_user.id:
            await message.answer(
                "⚠️ <b>Faqat o'zingizning raqamingizni yuborishingiz mumkin!</b>\n"
                "Boshqa shaxsning yoki forward qilingan kontaktlar qabul qilinmaydi. Iltimos, pastdagi «📱 Raqamni yuborish» tugmasini bosing:"
            )
            return
        new_phone = message.contact.phone_number
    elif message.text:
        import re
        phone_match = re.search(r"(\+?[0-9]{9,15})", message.text.replace(" ", "").replace("-", ""))
        if phone_match:
            new_phone = phone_match.group(1)

    if not new_phone:
        await message.answer("⚠️ Noto'g'ri telefon raqami. Iltimos, pastdagi «📱 Raqamni yuborish» tugmasini bosing yoki +998901234567 formatida yozing:")
        return

    async with async_session() as session:
        await session.execute(
            update(User).where(User.id == message.from_user.id).values(phone=new_phone)
        )
        await session.commit()

    await state.clear()
    await message.answer(
        f"✅ <b>Telefon raqamingiz muvaffaqiyatli yangilandi:</b> <code>{new_phone}</code>",
        reply_markup=main_menu_keyboard(
            i18n,
            user_id=message.from_user.id,
            user_name=message.from_user.full_name,
            username=message.from_user.username,
        ),
    )


# --- 👥 GURUHNI O'ZGARTIRISH SO'ROVI (TZ 6.3 & 7.6) ---

@router.callback_query(F.data == "settings:change_group")
async def start_group_change(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    async with async_session() as session:
        enr_res = await session.execute(
            select(Enrollment, Group, Course)
            .join(Group, Enrollment.group_id == Group.id)
            .join(Course, Group.course_id == Course.id)
            .where(Enrollment.student_id == user_id, Enrollment.is_active == True)
        )
        enr_row = enr_res.first()

        if not enr_row:
            await callback.answer("Siz hozirda faol guruhda emassiz.", show_alert=True)
            return

        current_enr, current_group, current_course = enr_row

        # Boshqa faol guruhlarni topamiz (bir xil kurs/daraja bo'yicha)
        other_groups_res = await session.execute(
            select(Group)
            .where(
                Group.course_id == current_course.id,
                Group.id != current_group.id,
                Group.is_active == True,
            )
        )
        other_groups = other_groups_res.scalars().all()

    if not other_groups:
        await callback.answer(
            "Hozirda ushbu kurs bo'yicha boshqa bo'sh guruhlar mavjud emas.", show_alert=True
        )
        return

    buttons = []
    for g in other_groups:
        buttons.append([
            InlineKeyboardButton(
                text=f"📌 {g.name} | Xona: {g.room or '101'}",
                callback_data=f"req_grp_target:{g.id}:{current_group.id}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="settings:back_to_menu")])

    await callback.message.edit_text(
        f"👥 <b>Guruhni O'zgartirish So'rovi</b>\n\n"
        f"Joriy guruhingiz: <b>{current_group.name}</b>\n"
        f"Qaysi yangi guruhga o'tmoqchisiz? Tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


from app.keyboards.main_menu import ALL_MAIN_MENU_TEXTS, main_menu_keyboard
from app.keyboards.admin_menu import ADMIN_PANEL_BUTTON_TEXTS, ADMIN_MENU_TEXTS
from app.handlers.teachers.admin_panel import open_admin_panel

ALL_NAV_BUTTONS = ALL_MAIN_MENU_TEXTS.union(ADMIN_PANEL_BUTTON_TEXTS).union(
    set(ADMIN_MENU_TEXTS.values())
).union({
    "👑 Admin Panel", "◀️ Asosiy menyu", "❌ Bekor qilish", "Bekor qilish", "/cancel",
    "Orqaga", "◀️ Orqaga", "◀️ Назад", "◀️ Back",
})


@router.callback_query(F.data.startswith("req_grp_target:"))
async def target_group_selected(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    target_group_id = int(parts[1])
    current_group_id = int(parts[2])

    await state.update_data(target_group_id=target_group_id, current_group_id=current_group_id)
    await state.set_state(SettingsFSM.group_change_reason)

    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="settings:cancel_group_change")]
    ])

    await callback.message.edit_text(
        "✍️ <b>Guruhni o'zgartirish sababini yozing:</b>\n"
        "<i>(Masalan: Dars vaqti to'g'ri kelmay qoldi yoki boshqa vaqtga o'tishim kerak)</i>\n\n"
        "<i>Bekor qilish uchun pastdagi tugmani bosing:</i>",
        reply_markup=cancel_kb,
    )
    await callback.answer()


@router.callback_query(F.data == "settings:cancel_group_change")
async def cancel_group_change_request(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "❌ <b>Guruhni o'zgartirish so'rovi bekor qilindi.</b>",
        reply_markup=main_menu_keyboard(
            i18n,
            user_id=callback.from_user.id,
            user_name=callback.from_user.full_name,
            username=callback.from_user.username,
        ),
    )
    await callback.answer()


@router.message(SettingsFSM.group_change_reason, F.text)
async def submit_group_change_reason(message: Message, state: FSMContext, i18n: I18nContext):
    raw_text = message.text.strip()

    # 1. Buyruqlar tekshiruvi
    if raw_text.startswith("/"):
        await state.clear()
        if raw_text in ("/admin", "/dashboard", "/panel"):
            return await open_admin_panel(message, i18n)
        await message.answer(
            "❌ Guruhni o'zgartirish so'rovi bekor qilindi.",
            reply_markup=main_menu_keyboard(
                i18n,
                user_id=message.from_user.id,
                user_name=message.from_user.full_name,
                username=message.from_user.username,
            ),
        )
        return

    # 2. Admin panel tugmasi tekshiruvi
    if raw_text in ADMIN_PANEL_BUTTON_TEXTS or "admin panel" in raw_text.lower():
        await state.clear()
        await message.answer("❌ Guruhni o'zgartirish so'rovi bekor qilindi.")
        return await open_admin_panel(message, i18n)

    # 3. Asosiy menyu va navigatsiya tugmalari tekshiruvi
    if raw_text in ALL_NAV_BUTTONS:
        await state.clear()
        await message.answer(
            "❌ Guruhni o'zgartirish so'rovi bekor qilindi.",
            reply_markup=main_menu_keyboard(
                i18n,
                user_id=message.from_user.id,
                user_name=message.from_user.full_name,
                username=message.from_user.username,
            ),
        )
        return

    # 4. Sabab uzunligi tekshiruvi
    if len(raw_text) < 5:
        cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="settings:cancel_group_change")]
        ])
        await message.answer(
            "⚠️ <b>Iltimos, guruhni almashtirish sababini to'liqroq yozing</b> (kamida 5 ta belgi).\n\n"
            "<i>Bekor qilish uchun pastdagi tugmani bosing:</i>",
            reply_markup=cancel_kb,
        )
        return

    reason = raw_text
    data = await state.get_data()
    target_group_id = data.get("target_group_id")
    current_group_id = data.get("current_group_id")
    await state.clear()

    async with async_session() as session:
        cur_grp = await session.get(Group, current_group_id)
        tar_grp = await session.get(Group, target_group_id)

        req = GroupChangeRequest(
            student_id=message.from_user.id,
            current_group_id=current_group_id,
            target_group_id=target_group_id,
            reason=reason,
            status="pending",
        )
        session.add(req)
        await session.commit()
        await session.refresh(req)

        teacher_id = tar_grp.teacher_id or (cur_grp.teacher_id if cur_grp else None)

    # O'qituvchi va adminlarga xabar yuborish
    from main import bot
    admin_ids = await get_admin_ids()
    notif_recipients = set(admin_ids)
    if teacher_id:
        notif_recipients.add(teacher_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ruxsat berish", callback_data=f"grp_chg_acc:{req.id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"grp_chg_rej:{req.id}"),
        ]
    ])

    admin_text = (
        f"👥 <b>Guruhni O'zgartirish So'rovi #{req.id}</b>\n\n"
        f"👤 <b>O'quvchi:</b> {message.from_user.full_name} (@{message.from_user.username or 'yoq'})\n"
        f"⬅️ <b>Eski guruh:</b> {cur_grp.name if cur_grp else current_group_id}\n"
        f"➡️ <b>Yangi guruh:</b> {tar_grp.name if tar_grp else target_group_id}\n"
        f"📝 <b>Sabab:</b> <i>{reason}</i>"
    )

    for uid in notif_recipients:
        try:
            await bot.send_message(chat_id=uid, text=admin_text, reply_markup=keyboard)
        except Exception:
            pass

    await message.answer(
        "✅ <b>Guruhni o'zgartirish so'rovingiz qabul qilindi!</b>\n"
        "O'qituvchi va ma'muriyat ko'rib chiqib, sizga javobini yuboradi.",
        reply_markup=main_menu_keyboard(
            i18n,
            user_id=message.from_user.id,
            user_name=message.from_user.full_name,
            username=message.from_user.username,
        ),
    )


# --- 💰 QAYTARISH (REFUND) SO'ROVI (TZ 9.3) ---

@router.callback_query(F.data == "settings:refund")
async def start_refund_request(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    async with async_session() as session:
        enr_res = await session.execute(
            select(Enrollment, Group, Course)
            .join(Group, Enrollment.group_id == Group.id)
            .join(Course, Group.course_id == Course.id)
            .where(Enrollment.student_id == user_id, Enrollment.is_active == True)
        )
        enr_row = enr_res.first()

        if not enr_row:
            await callback.answer("Siz hozirda biror guruhda faol emassiz.", show_alert=True)
            return

        enr, group, course = enr_row

        # To'lov ma'lumotlarini olamiz
        pay_res = await session.execute(
            select(Payment).where(
                Payment.student_id == user_id,
                Payment.group_id == group.id,
                Payment.status == PaymentStatusEnum.confirmed,
            ).order_by(Payment.paid_at.desc())
        )
        payment = pay_res.scalar_one_or_none()
        paid_amount = float(payment.amount) if payment else float(course.price)

        # Qatnashgan darslar soni (davomatdan)
        att_res = await session.execute(
            select(Attendance).where(
                Attendance.student_id == user_id,
                Attendance.group_id == group.id,
                Attendance.status.in_([AttendanceStatusEnum.present, AttendanceStatusEnum.late]),
            )
        )
        attended_count = len(att_res.scalars().all())

        price_per_lesson = float(course.price_per_lesson or (course.price / 12))
        used_amount = attended_count * price_per_lesson
        calculated_refund = max(0.0, paid_amount - used_amount)

    await state.update_data(
        payment_id=payment.id if payment else None,
        group_id=group.id,
        paid_amount=paid_amount,
        attended_count=attended_count,
        price_per_lesson=price_per_lesson,
        calculated_refund=calculated_refund,
    )
    await state.set_state(SettingsFSM.refund_reason)

    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="settings:cancel_refund")]
    ])

    text = (
        f"💰 <b>To'lovni Qaytarish (Refund) Hisob-kitobi</b>\n\n"
        f"📚 <b>Guruh:</b> {group.name}\n"
        f"💵 <b>To'langan summa:</b> {paid_amount:,.0f} so'm\n"
        f"📅 <b>Qatnashilgan darslar:</b> {attended_count} ta\n"
        f"💳 <b>1 dars narxi:</b> {price_per_lesson:,.0f} so'm\n"
        f"⚖️ <b>Qaytariladigan summa:</b> <b>{calculated_refund:,.0f} so'm</b>\n\n"
        f"<i>Formula: {paid_amount:,.0f} - ({attended_count} × {price_per_lesson:,.0f}) = {calculated_refund:,.0f} so'm</i>\n\n"
        f"✍️ <b>Kursdan chiqish va to'lovni qaytarish sababini yozing:</b>\n"
        f"<i>(Bekor qilish uchun pastdagi tugmani bosing)</i>"
    )

    await callback.message.edit_text(text, reply_markup=cancel_kb)
    await callback.answer()


@router.callback_query(F.data == "settings:cancel_refund")
async def cancel_refund_request(callback: CallbackQuery, state: FSMContext, i18n: I18nContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "❌ <b>To'lovni qaytarish (Refund) so'rovi bekor qilindi.</b>",
        reply_markup=main_menu_keyboard(
            i18n,
            user_id=callback.from_user.id,
            user_name=callback.from_user.full_name,
            username=callback.from_user.username,
        ),
    )
    await callback.answer()


@router.message(SettingsFSM.refund_reason, F.text)
async def submit_refund_reason(message: Message, state: FSMContext, i18n: I18nContext):
    raw_text = message.text.strip()

    # 1. Buyruqlar tekshiruvi
    if raw_text.startswith("/"):
        await state.clear()
        if raw_text in ("/admin", "/dashboard", "/panel"):
            return await open_admin_panel(message, i18n)
        await message.answer(
            "❌ Qaytarish (Refund) so'rovi bekor qilindi.",
            reply_markup=main_menu_keyboard(
                i18n,
                user_id=message.from_user.id,
                user_name=message.from_user.full_name,
                username=message.from_user.username,
            ),
        )
        return

    # 2. Admin Panel tugmasi tekshiruvi
    if raw_text in ADMIN_PANEL_BUTTON_TEXTS or "admin panel" in raw_text.lower():
        await state.clear()
        await message.answer("❌ Qaytarish (Refund) so'rovi bekor qilindi.")
        return await open_admin_panel(message, i18n)

    # 3. Asosiy menyu va navigatsiya tugmalari tekshiruvi
    if raw_text in ALL_NAV_BUTTONS:
        await state.clear()
        await message.answer(
            "❌ Qaytarish (Refund) so'rovi bekor qilindi.",
            reply_markup=main_menu_keyboard(
                i18n,
                user_id=message.from_user.id,
                user_name=message.from_user.full_name,
                username=message.from_user.username,
            ),
        )
        return

    # 4. Sabab uzunligi tekshiruvi
    if len(raw_text) < 5:
        cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="settings:cancel_refund")]
        ])
        await message.answer(
            "⚠️ <b>Iltimos, qaytarish sababini to'liqroq yozing</b> (kamida 5 ta belgi).\n\n"
            "<i>Masalan: Ish jadvalim o'zgarganligi sababli darslarga qatnasha olmayman.</i>\n\n"
            "<i>Bekor qilish uchun pastdagi tugmani bosing:</i>",
            reply_markup=cancel_kb,
        )
        return

    reason = raw_text
    data = await state.get_data()
    payment_id = data.get("payment_id")
    group_id = data.get("group_id")
    calculated_refund = data.get("calculated_refund", 0.0)
    paid_amount = data.get("paid_amount", 0.0)
    attended_count = data.get("attended_count", 0)
    await state.clear()

    async with async_session() as session:
        group = await session.get(Group, group_id)
        refund = Refund(
            payment_id=payment_id,
            student_id=message.from_user.id,
            group_id=group_id,
            reason=reason,
            calculated_amount=calculated_refund,
            status="pending",
        )
        session.add(refund)
        await session.commit()
        await session.refresh(refund)

    # Adminlarga yuborish
    from main import bot
    admin_ids = await get_admin_ids()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Qaytarishni Tasdiqlash", callback_data=f"ref_adm_acc:{refund.id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"ref_adm_rej:{refund.id}"),
        ]
    ])

    admin_text = (
        f"💰 <b>Qaytarish (Refund) So'rovi #{refund.id}</b>\n\n"
        f"👤 <b>O'quvchi:</b> {message.from_user.full_name} (@{message.from_user.username or 'yoq'})\n"
        f"📚 <b>Guruh:</b> {group.name if group else group_id}\n"
        f"💵 <b>To'langan:</b> {paid_amount:,.0f} so'm\n"
        f"📅 <b>Qatnashgan:</b> {attended_count} dars\n"
        f"⚖️ <b>Qaytariladigan summa:</b> <b>{calculated_refund:,.0f} so'm</b>\n"
        f"📝 <b>Sabab:</b> <i>{reason}</i>"
    )

    for uid in admin_ids:
        try:
            await bot.send_message(chat_id=uid, text=admin_text, reply_markup=keyboard)
        except Exception:
            pass

    await message.answer(
        f"✅ <b>Qaytarish so'rovingiz qabul qilindi (#{refund.id})!</b>\n\n"
        f"Hisoblangan summa: <b>{calculated_refund:,.0f} so'm</b>\n"
        f"Adminlar tekshirib chiqqach, pul qaytariladi va sizga xabar beriladi.",
        reply_markup=main_menu_keyboard(
            i18n,
            user_id=message.from_user.id,
            user_name=message.from_user.full_name,
            username=message.from_user.username,
        ),
    )


@router.callback_query(F.data == "settings:back_to_menu")
@router.callback_query(F.data == "settings:close")
async def back_to_settings(callback: CallbackQuery, i18n: I18nContext):
    await callback.message.delete()
    await callback.message.answer(
        "Asosiy menyudasiz:",
        reply_markup=main_menu_keyboard(
            i18n,
            user_id=callback.from_user.id,
            user_name=callback.from_user.full_name,
            username=callback.from_user.username,
        ),
    )
    await callback.answer()
