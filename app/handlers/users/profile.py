"""
👤 Profilim bo'limi (TZ v2.6, 16.1-bo'lim & 15 Gamification).
- Kursda o'qimasa: Stikerli karta, ma'lumotlar, referal kod, badge'lar + Free darsga yozilish tugmasi
- Kursda o'qisa: Kurs nomi, o'qituvchi username linki, guruh chatiga havola, to'lov holati, badge'lar
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions
from aiogram_i18n import I18nContext
from sqlalchemy import select

from backend.database import async_session
from backend.models import User, Enrollment, Group, Course, Payment, PaymentStatusEnum
from backend.services.gamification import get_user_badges_summary
from backend.utils.formatters import format_schedule

router = Router()

PROFILE_BUTTON_TEXTS = {
    "👤 Profilim", "👤 Мой профиль", "👤 My Profile",
    "Profilim", "Мой профиль", "My Profile", "Profile", "Profil",
}


@router.message(Command("profile"))
@router.message(F.text.in_(PROFILE_BUTTON_TEXTS))
async def show_profile(message: Message, i18n: I18nContext):
    user_id = message.from_user.id
    lang = getattr(i18n, "locale", "uz") or "uz"

    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            # Agar foydalanuvchi bazada hali yo'q bo'lsa, yaratamiz
            user = User(
                id=user_id,
                full_name=message.from_user.full_name or "Foydalanuvchi",
                username=message.from_user.username,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            # Foydalanuvchi Telegram ma'lumotlarini eng so'nggi holatga sinxronizatsiya qilamiz
            updated = False
            real_username = message.from_user.username
            if user.username != real_username:
                user.username = real_username
                updated = True
            if message.from_user.full_name and user.full_name in ("Bosh Admin", "Foydalanuvchi", None, ""):
                user.full_name = message.from_user.full_name
                updated = True
            if updated:
                await session.commit()
                await session.refresh(user)

        # Faol yozilish (Enrollment) ni tekshiramiz
        enrollment_res = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == user_id,
                Enrollment.is_active == True,
            ).order_by(Enrollment.enrolled_at.desc())
        )
        enrollment = enrollment_res.scalars().first()

        group = None
        course = None
        teacher = None
        payment = None

        if enrollment:
            group = await session.get(Group, enrollment.group_id)
            if group:
                course = await session.get(Course, group.course_id)
                teacher = await session.get(User, group.teacher_id) if group.teacher_id else None

            pay_res = await session.execute(
                select(Payment).where(
                    Payment.student_id == user_id,
                    Payment.group_id == enrollment.group_id,
                ).order_by(Payment.created_at.desc())
            )
            payment = pay_res.scalars().first()

        # Badges list
        badges = await get_user_badges_summary(user_id)

    # Sana formati
    created_date = user.created_at.strftime("%d.%m.%Y") if user.created_at else "-"
    actual_username = message.from_user.username if (message.from_user and message.from_user.username) else user.username
    if actual_username and actual_username != "admin":
        username_str = f"@{actual_username}"
    elif user.username and user.username != "admin":
        username_str = f"@{user.username}"
    else:
        username_str = "Mavjud emas"
    user_name_link = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"
    badges_str = " • ".join(badges) if badges else "Boshlang'ich"

    if not enrollment or not group or not course:
        # Kursda o'qimaydigan o'quvchi profili
        ref_code = user.referral_code or f"REF{user.id}"
        lang_str = user.language.value.upper() if hasattr(user.language, "value") else str(user.language or "UZ").upper()
        text = (
            f"👤 <b>Foydalanuvchi Profili</b>\n\n"
            f"▫️ <b>Ism:</b> {user_name_link}\n"
            f"▫️ <b>Username:</b> {username_str}\n"
            f"▫️ <b>Telegram ID:</b> <code>{user.id}</code>\n"
            f"▫️ <b>Telefon:</b> {user.phone or 'Kiritilmagan'}\n"
            f"▫️ <b>Til:</b> {lang_str}\n"
            f"▫️ <b>Ro'yxatdan o'tgan sana:</b> {created_date}\n"
            f"▫️ <b>Referal kodingiz:</b> <code>{ref_code}</code>\n"
            f"▫️ <b>Yutuqlar / Badges:</b> {badges_str}\n\n"
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
        level_str = course.level.value if hasattr(course.level, "value") else str(course.level)
        schedule_str = format_schedule(group.schedule, lang)

        # Teacher link
        if teacher and teacher.username and teacher.username != "admin":
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
            f"📚 <b>Kurs:</b> {course_title} ({level_str})\n"
            f"👥 <b>Guruh:</b> {group.name}\n"
            f"👨‍🏫 <b>O'qituvchi:</b> {teacher_link_str}\n"
            f"🗓 <b>Dars jadvali:</b> {schedule_str}\n"
            f"💬 <b>Guruh chati:</b> {group_chat_str}\n"
            f"💳 <b>To'lov holati:</b> {payment_status_str}\n"
            f"🎖 <b>Yutuqlar / Badges:</b> {badges_str}\n\n"
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
