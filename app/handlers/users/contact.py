"""
📞 Bog'lanish va Jonli Savol-Javob (TZ v2.6, 16.2-bo'lim).
- Markaz kontaktlari `center_settings` jadvalidan dinamik olinadi
- Jonli support chat (proksi xabarlar)
- 15 daqiqa faolsizlik bo'lsa chat avtomatik yopiladi
"""
from datetime import datetime
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram_i18n import I18nContext
from sqlalchemy import select, update

from backend.database import async_session
from backend.models import (
    CenterSetting,
    SupportChat,
    SupportChatStatusEnum,
    SupportChatClosedReasonEnum,
    User,
    Enrollment,
    Group,
    Course,
)
from backend.services.user_service import get_admin_ids
from app.state.support import SupportState
from app.keyboards.main_menu import main_menu_keyboard

router = Router()

CONTACT_BUTTON_TEXTS = {"📞 Bog'lanish", "📞 Контакты", "📞 Contact"}
CANCEL_BUTTON_TEXTS = {"◀️ Bekor qilish", "◀️ Отмена", "◀️ Cancel"}


@router.message(F.text.in_(CONTACT_BUTTON_TEXTS))
async def show_contacts(message: Message, i18n: I18nContext):
    if not message.from_user:
        return
    lang = i18n.locale

    async with async_session() as session:
        result = await session.execute(select(CenterSetting).limit(1))
        settings = result.scalar_one_or_none()

    if not settings:
        phone = "+998 90 123 45 67"
        admin_user = "english_center_admin"
        address = "Toshkent shahri, Amir Temur ko'chasi"
    else:
        phone = settings.contact_phone
        admin_user = settings.contact_username
        address = settings.address.get(lang, settings.address.get("uz", "Toshkent")) if isinstance(settings.address, dict) else str(settings.address)

    text = (
        f"📞 <b>O'quv Markazi Kontaktlari:</b>\n\n"
        f"☎️ <b>Telefon:</b> {phone}\n"
        f"✍️ <b>Admin:</b> @{admin_user}\n"
        f"📍 <b>Manzil:</b> {address}\n\n"
        f"Savolingiz bo'lsa, quyidagi tugma orqali to'g'ridan-to'g'ri yozishingiz mumkin:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❓ Savol berish", callback_data="start_support_chat")]
    ])
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "start_support_chat")
async def start_support_chat(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportState.writing_question)
    cancel_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="◀️ Bekor qilish")]],
        resize_keyboard=True,
    )
    await callback.message.answer(
        "✍️ Savolingizni batafsil yozing. Bizning menejerlarimiz tez orada bot orqali javob berishadi.\n\n"
        "<i>Bekor qilish uchun pastdagi «◀️ Bekor qilish» tugmasini bosing:</i>",
        reply_markup=cancel_kb,
    )
    await callback.answer()


@router.message(SupportState.writing_question, F.text.in_(CANCEL_BUTTON_TEXTS))
async def cancel_support_question(message: Message, state: FSMContext, i18n: I18nContext):
    await state.clear()
    await message.answer(
        "Murojaat bekor qilindi.",
        reply_markup=main_menu_keyboard(i18n),
    )


MAIN_MENU_BUTTONS_ALL = {
    "👤 Profilim", "👤 Мой профиль", "👤 My Profile",
    "📚 Kurslar", "📚 Курсы", "📚 Courses",
    "📝 Free darsga yozilish", "📝 Записаться на пробный урок", "📝 Sign up for a trial lesson",
    "📖 Uyga vazifa", "📖 Домашнее задание", "📖 Homework",
    "📊 Davomat", "📊 Посещаемость", "📊 Attendance",
    "🏆 Reyting", "🏆 Рейтинг", "🏆 Leaderboard",
    "👥 Referal", "👥 Реферал", "👥 Referral",
    "📞 Bog'lanish", "📞 Контакты", "📞 Contact",
}


@router.message(SupportState.writing_question, F.text)
async def question_received(message: Message, state: FSMContext, i18n: I18nContext):
    if not message.from_user or not message.text:
        return

    text_stripped = message.text.strip()

    # Agar foydalanuvchi menyu tugmasini bosgan bo'lsa yoki bekor qilmoqchi bo'lsa
    if text_stripped in MAIN_MENU_BUTTONS_ALL or text_stripped in CANCEL_BUTTON_TEXTS or text_stripped.startswith("/"):
        await state.clear()
        if text_stripped in CONTACT_BUTTON_TEXTS:
            await show_contacts(message, i18n)
        else:
            await message.answer(
                "Muloqot bekor qilindi.",
                reply_markup=main_menu_keyboard(i18n),
            )
        return

    student_id = message.from_user.id
    student_name = message.from_user.full_name
    question_text = message.text

    # O'quvchi va uning guruhi ma'lumotlarini olamiz
    group_info_str = "Hozircha kursda o'qimaydi"
    phone_str = "Kiritilmagan"

    async with async_session() as session:
        user = await session.get(User, student_id)
        if user and user.phone:
            phone_str = user.phone

        enrollment_res = await session.execute(
            select(Enrollment)
            .where(Enrollment.student_id == student_id, Enrollment.is_active == True)
            .order_by(Enrollment.enrolled_at.desc())
        )
        enrollment = enrollment_res.scalar_one_or_none()

        if enrollment:
            group = await session.get(Group, enrollment.group_id)
            if group:
                course = await session.get(Course, group.course_id)
                course_lvl = course.level.value if course else ""
                group_info_str = f"<b>{group.name}</b> ({course_lvl})"

        chat = SupportChat(
            student_id=student_id,
            status=SupportChatStatusEnum.open,
            last_message_by="student",
            last_message_at=datetime.utcnow(),
        )
        session.add(chat)
        await session.commit()
        chat_id = chat.id

    await state.clear()
    await message.answer(
        "✅ <b>Savolingiz qabul qilindi!</b>\n\n"
        "Tez orada menejerlarimiz sizga shu yerda javob berishadi.",
        reply_markup=main_menu_keyboard(i18n),
    )

    # Adminlarga yuborish
    from main import bot
    admin_ids = await get_admin_ids()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 Javob berish", callback_data=f"support_reply:{chat_id}:{student_id}"),
            InlineKeyboardButton(text="🔒 Yopish", callback_data=f"support_close:{chat_id}"),
        ]
    ])
    
    # Username bo'lsa @username, bo'lmasa to'g'ridan-to'g'ri profiliga o'tuvchi tg://user?id linki
    if message.from_user.username:
        username_str = f"@{message.from_user.username}"
    else:
        username_str = f"<a href='tg://user?id={student_id}'>Profil havolasi (username yo'q)</a>"

    student_link_str = f"<a href='tg://user?id={student_id}'>{student_name}</a>"
    
    text = (
        f"❓ <b>Yangi Xabar Keldi (Muloqot #{chat_id}):</b>\n\n"
        f"👤 <b>O'quvchi:</b> {student_link_str}\n"
        f"📱 <b>Telefon:</b> {phone_str}\n"
        f"🌐 <b>Username:</b> {username_str}\n"
        f"🆔 <b>Telegram ID:</b> <code>{student_id}</code>\n"
        f"📚 <b>Guruh holati:</b> {group_info_str}\n\n"
        f"💬 <b>Xabar matni:</b>\n{question_text}"
    )

    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, text, reply_markup=keyboard)
        except Exception:
            continue


@router.callback_query(F.data.startswith("support_reply:"))
async def support_reply_callback(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    chat_id = int(parts[1])
    student_id = int(parts[2])

    await state.update_data(chat_id=chat_id, student_id=student_id)
    await state.set_state(SupportState.in_chat)
    await callback.message.answer(
        f"✍️ O'quvchiga (ID: <code>{student_id}</code>) javobingizni yozing:\n\n"
        f"<i>Suhbatni yopish uchun pastdagi tugmani bosing:</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔒 Suhbatni yakunlash", callback_data=f"support_close:{chat_id}")]
        ]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("student_reply:"))
async def student_reply_callback(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split(":")[1])
    await state.update_data(chat_id=chat_id)
    await state.set_state(SupportState.writing_question)
    cancel_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="◀️ Bekor qilish")]],
        resize_keyboard=True,
    )
    await callback.message.answer(
        "✍️ Adminga javobingizni yoki qo'shimcha savolingizni yozing:\n\n"
        "<i>Bekor qilish uchun pastdagi «◀️ Bekor qilish» tugmasini bosing:</i>",
        reply_markup=cancel_kb,
    )
    await callback.answer()


@router.message(SupportState.in_chat, F.text)
async def admin_message_sent(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    student_id = data.get("student_id")

    if not student_id or not chat_id:
        await state.clear()
        return

    from main import bot
    # O'quvchiga javob yozish tugmasi bilan yetkazamiz
    student_reply_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Javob yozish", callback_data=f"student_reply:{chat_id}")]
    ])

    try:
        await bot.send_message(
            student_id,
            f"💬 <b>Admin javobi:</b>\n\n{message.text}\n\n<i>Javob yozish uchun pastdagi tugmani bosing:</i>",
            reply_markup=student_reply_kb,
        )
        await state.clear()
        await message.answer(
            "✅ Javobingiz o'quvchiga yetkazildi.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="💬 Yana yozish", callback_data=f"support_reply:{chat_id}:{student_id}"),
                    InlineKeyboardButton(text="🔒 Suhbatni yakunlash", callback_data=f"support_close:{chat_id}"),
                ]
            ]),
        )

        async with async_session() as session:
            await session.execute(
                update(SupportChat)
                .where(SupportChat.id == chat_id)
                .values(last_message_by="admin", last_message_at=datetime.utcnow(), admin_id=message.from_user.id)
            )
            await session.commit()
    except Exception as e:
        await message.answer(f"Xatolik: O'quvchiga yuborib bo'lmadi ({e})")


@router.callback_query(F.data.startswith("support_close:"))
async def close_support_chat(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        chat = await session.get(SupportChat, chat_id)
        if chat and chat.status == SupportChatStatusEnum.open:
            chat.status = SupportChatStatusEnum.closed
            chat.closed_at = datetime.utcnow()
            chat.closed_reason = SupportChatClosedReasonEnum.resolved
            await session.commit()

            from main import bot
            try:
                await bot.send_message(
                    chat.student_id,
                    "🔒 Muloqot yakunlandi. Agar yana savollaringiz bo'lsa, bemalol murojaat qiling!"
                )
            except Exception:
                pass

    await state.clear()
    await callback.message.edit_text("✅ Suhbat muvaffaqiyatli yakunlandi va yopildi.")
    await callback.answer("Suhbat yopildi.")
