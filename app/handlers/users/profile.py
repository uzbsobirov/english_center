"""
👤 Profilim bo'limi (TZ v2.6, 16.1-bo'lim).
- Kursda o'qimasa: Stikerli karta, ma'lumotlar, referal kod + Free darsga yozilish tugmasi
- Kursda o'qisa: Kurs nomi, o'qituvchi username linki, guruh chatiga havola, to'lov holati
"""
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions
from aiogram_i18n import I18nContext
from sqlalchemy import select

from backend.database import async_session
from backend.models import User, Enrollment, Group, Course, Payment, PaymentStatusEnum

router = Router()

PROFILE_BUTTON_TEXTS = {"👤 Profilim", "👤 Мой профиль", "👤 My Profile"}


@router.message(F.text.in_(PROFILE_BUTTON_TEXTS))
async def show_profile(message: Message, i18n: I18nContext):
    user_id = message.from_user.id
    lang = i18n.locale

    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            await message.answer("Foydalanuvchi ma'lumotlari topilmadi.")
            return

        # Faol yozilish (Enrollment) ni tekshiramiz
        enrollment_res = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == user_id,
                Enrollment.is_active == True,
            ).order_by(Enrollment.enrolled_at.desc())
        )
        enrollment = enrollment_res.scalar_one_or_none()

        group = None
        course = None
        teacher = None
        payment = None

        if enrollment:
            group = await session.get(Group, enrollment.group_id)
            if group:
                course = await session.get(Course, group.course_id)
                teacher = await session.get(User, group.teacher_id)

            pay_res = await session.execute(
                select(Payment).where(
                    Payment.student_id == user_id,
                    Payment.group_id == enrollment.group_id,
                ).order_by(Payment.created_at.desc())
            )
            payment = pay_res.scalar_one_or_none()

    # Sana formati
    created_date = user.created_at.strftime("%d.%m.%Y") if user.created_at else "-"
    username_str = f"@{user.username}" if user.username else "Mavjud emas"
    user_name_link = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"

    if not enrollment or not group or not course:
        # Kursda o'qimaydigan o'quvchi profili
        ref_code = user.referral_code or f"REF{user.id}"
        lang_str = user.language.value.upper() if hasattr(user.language, "value") else str(user.language).upper()
        text = (
            f"👤 <b>Foydalanuvchi Profili</b>\n\n"
            f"▫️ <b>Ism:</b> {user_name_link}\n"
            f"▫️ <b>Username:</b> {username_str}\n"
            f"▫️ <b>Telegram ID:</b> <code>{user.id}</code>\n"
            f"▫️ <b>Telefon:</b> {user.phone or 'Kiritilmagan'}\n"
            f"▫️ <b>Til:</b> {lang_str}\n"
            f"▫️ <b>Ro'yxatdan o'tgan sana:</b> {created_date}\n"
            f"▫️ <b>Referal kodingiz:</b> <code>{ref_code}</code>\n\n"
            f"ℹ️ <i>Siz hozircha hech qaysi kursga yozilmagansiz.</i>"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Free darsga yozilish", callback_data="start_free_trial_flow")]
        ])
        await message.answer(
            text,
            reply_markup=keyboard,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    else:
        # Kursda faol o'qiydigan o'quvchi profili
        course_title = course.title.get(lang, course.title.get("uz", "")) if isinstance(course.title, dict) else str(course.title)
        
        # Teacher link
        if teacher and teacher.username:
            teacher_link_str = f"@{teacher.username} ({teacher.full_name})"
        elif teacher:
            teacher_link_str = f"<a href='tg://user?id={teacher.id}'>{teacher.full_name}</a>"
        else:
            teacher_link_str = "Tayinlanmagan"

        # Group chat link
        group_chat_str = f"<a href='{group.group_chat_link}'>Guruh chatiga kirish 🔗</a>" if group.group_chat_link else "Havola yo'q"

        # To'lov holati
        if payment and payment.status == PaymentStatusEnum.confirmed:
            payment_status_str = f"✅ To'langan ({float(payment.amount):,.0f} so'm)"
        elif payment and payment.status == PaymentStatusEnum.pending:
            payment_status_str = "⏳ Tasdiqlash jarayonida"
        else:
            payment_status_str = "❌ To'lanmagan"

        text = (
            f"🎓 <b>O'quvchi Profili</b>\n\n"
            f"👤 <b>Ism:</b> {user_name_link}\n"
            f"🌐 <b>Username:</b> {username_str}\n"
            f"🆔 <b>Telegram ID:</b> <code>{user.id}</code>\n"
            f"📱 <b>Telefon:</b> {user.phone or 'Kiritilmagan'}\n"
            f"📚 <b>Kurs:</b> {course_title} ({course.level.value})\n"
            f"👥 <b>Guruh:</b> {group.name}\n"
            f"👨‍🏫 <b>O'qituvchi:</b> {teacher_link_str}\n"
            f"💬 <b>Guruh chati:</b> {group_chat_str}\n"
            f"💳 <b>To'lov holati:</b> {payment_status_str}\n\n"
            f"📅 <b>A'zo bo'lingan sana:</b> {enrollment.enrolled_at.strftime('%d.%m.%Y')}"
        )
        
        buttons = []
        if group.group_chat_link:
            buttons.append([InlineKeyboardButton(text="👥 Guruh Telegram Chati", url=group.group_chat_link)])
        if payment and payment.status != PaymentStatusEnum.confirmed:
            buttons.append([InlineKeyboardButton(text="💳 To'lov qilish", callback_data=f"pay_group:{group.id}")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
        await message.answer(
            text,
            reply_markup=keyboard,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
