"""
📋 Uy Vazifam bo'limi (TZ v2.6, 16.4-bo'lim).
- Guruhda o'qimasa: «Siz hozircha hech qaysi kursda o'qimayapsiz» + Free dars tugmasi
- Guruhda o'qisa: Faol uy vazifalari ro'yxati, muddati va biriktirilgan fayllarni yuklab olish
"""
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_i18n import I18nContext
from sqlalchemy import select

from backend.database import async_session
from backend.models import Enrollment, Homework, Group, User

router = Router()

HOMEWORK_BUTTON_TEXTS = {"📋 Uy Vazifam", "📋 Домашнее задание", "📋 Homework"}


@router.message(F.text.in_(HOMEWORK_BUTTON_TEXTS))
async def show_homework(message: Message, i18n: I18nContext):
    user_id = message.from_user.id
    lang = getattr(i18n, "locale", "uz") or "uz"

    async with async_session() as session:
        # O'quvchining faol guruhini topamiz
        enrollment_res = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == user_id,
                Enrollment.is_active == True,
            ).order_by(Enrollment.enrolled_at.desc())
        )
        enrollment = enrollment_res.scalar_one_or_none()

        if not enrollment:
            if lang == "uz":
                not_enrolled_text = (
                    "📚 <b>Siz hozircha hech qaysi guruhda o'qimayapsiz.</b>\n\n"
                    "Guruhga a'zo bo'lish va dars materiallaridan foydalanish uchun bepul sinov darsiga yoziling:"
                )
                free_btn_text = "📝 Free darsga yozilish"
            elif lang == "ru":
                not_enrolled_text = (
                    "📚 <b>Вы пока не состоите ни в одной группе.</b>\n\n"
                    "Запишитесь на бесплатный пробный урок, чтобы присоединиться к группе:"
                )
                free_btn_text = "📝 Запись на бесплатный урок"
            else:
                not_enrolled_text = (
                    "📚 <b>You are not currently enrolled in any active group.</b>\n\n"
                    "Book a free trial lesson to join a course group:"
                )
                free_btn_text = "📝 Book free lesson"

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=free_btn_text, callback_data="start_free_trial_flow")]
            ])
            await message.answer(not_enrolled_text, reply_markup=keyboard)
            return

        group = await session.get(Group, enrollment.group_id)

        # Guruhning eng so'nggi 5 ta uy vazifasini olamiz
        hw_res = await session.execute(
            select(Homework).where(
                Homework.group_id == enrollment.group_id
            ).order_by(Homework.created_at.desc()).limit(5)
        )
        homeworks = hw_res.scalars().all()

    if not homeworks:
        empty_msg = (
            f"📋 <b>{group.name if group else 'Guruh'}</b> bo'yicha hozircha yangi uy vazifalari yo'q. Baraka toping! 🎉"
            if lang == "uz"
            else (
                f"📋 По группе <b>{group.name if group else 'Группа'}</b> пока нет активных домашних заданий. 🎉"
                if lang == "ru"
                else f"📋 No active homework assignments for <b>{group.name if group else 'Group'}</b>. Well done! 🎉"
            )
        )
        await message.answer(empty_msg)
        return

    now = datetime.utcnow()
    latest_hw = homeworks[0]
    is_latest_active = latest_hw.due_at and latest_hw.due_at >= now

    due_str = latest_hw.due_at.strftime("%d.%m.%Y %H:%M") if latest_hw.due_at else "-"
    status_tag = "🟢 <b>Faol</b>" if is_latest_active else "⏳ <b>Muddati yakunlangan</b>"

    lines = [
        f"📋 <b>{group.name} guruhi — Joriy Uy Vazifasi</b>\n",
        f"📌 <b>Mavzu:</b> <b>{latest_hw.title}</b>",
        f"📊 <b>Holat:</b> {status_tag}",
        f"⏳ <b>Topshirish muddati:</b> {due_str}",
        f"📝 <b>Tavsif / Vazifa:</b>\n{latest_hw.description or 'Izoh kiritilmagan'}"
    ]

    buttons = []
    if latest_hw.file_id:
        buttons.append([InlineKeyboardButton(
            text="📥 Vazifa faylini yuklab olish",
            callback_data=f"get_hw_file:{latest_hw.id}"
        )])

    # Agar oldingi vazifalar mavjud bo'lsa, alohida tugma qo'shamiz
    if len(homeworks) > 1:
        buttons.append([InlineKeyboardButton(
            text="📁 Oldingi uy vazifalari tarixi",
            callback_data=f"hw_history:{group.id}"
        )])

    full_text = "\n".join(lines)
    reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
    await message.answer(full_text, reply_markup=reply_markup)


@router.callback_query(F.data.startswith("show_current_hw:"))
async def show_current_hw_callback(callback: CallbackQuery):
    group_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        group = await session.get(Group, group_id)
        hw_res = await session.execute(
            select(Homework).where(
                Homework.group_id == group_id
            ).order_by(Homework.created_at.desc()).limit(5)
        )
        homeworks = hw_res.scalars().all()

    if not homeworks:
        await callback.answer("Vazifalar topilmadi.", show_alert=True)
        return

    now = datetime.utcnow()
    latest_hw = homeworks[0]
    is_latest_active = latest_hw.due_at and latest_hw.due_at >= now
    due_str = latest_hw.due_at.strftime("%d.%m.%Y %H:%M") if latest_hw.due_at else "-"
    status_tag = "🟢 <b>Faol</b>" if is_latest_active else "⏳ <b>Muddati yakunlangan</b>"

    lines = [
        f"📋 <b>{group.name} guruhi — Joriy Uy Vazifasi</b>\n",
        f"📌 <b>Mavzu:</b> <b>{latest_hw.title}</b>",
        f"📊 <b>Holat:</b> {status_tag}",
        f"⏳ <b>Topshirish muddati:</b> {due_str}",
        f"📝 <b>Tavsif / Vazifa:</b>\n{latest_hw.description or 'Izoh kiritilmagan'}"
    ]

    buttons = []
    if latest_hw.file_id:
        buttons.append([InlineKeyboardButton(
            text="📥 Vazifa faylini yuklab olish",
            callback_data=f"get_hw_file:{latest_hw.id}"
        )])

    if len(homeworks) > 1:
        buttons.append([InlineKeyboardButton(
            text="📁 Oldingi uy vazifalari tarixi",
            callback_data=f"hw_history:{group.id}"
        )])

    full_text = "\n".join(lines)
    await callback.message.edit_text(full_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("hw_history:"))
async def show_hw_history_callback(callback: CallbackQuery):
    group_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        group = await session.get(Group, group_id)
        hw_res = await session.execute(
            select(Homework).where(
                Homework.group_id == group_id
            ).order_by(Homework.created_at.desc()).limit(10)
        )
        homeworks = hw_res.scalars().all()

    if len(homeworks) <= 1:
        await callback.answer("Oldingi vazifalar mavjud emas.", show_alert=True)
        return

    past_homeworks = homeworks[1:]
    lines = [
        f"📁 <b>{group.name if group else 'Guruh'} — Oldingi Uy Vazifalari Tarixi</b>\n"
    ]

    buttons = []
    for idx, hw in enumerate(past_homeworks, 1):
        due_str = hw.due_at.strftime("%d.%m.%Y") if hw.due_at else "-"
        lines.append(f"<b>{idx}. {hw.title}</b>")
        lines.append(f"   ⏳ Topshirish muddati: {due_str}")
        if hw.description:
            desc_short = hw.description[:60] + "..." if len(hw.description) > 60 else hw.description
            lines.append(f"   📝 {desc_short}")
        lines.append("")

        if hw.file_id:
            buttons.append([InlineKeyboardButton(
                text=f"📎 Fayl: {hw.title[:25]}",
                callback_data=f"get_hw_file:{hw.id}"
            )])

    buttons.append([InlineKeyboardButton(
        text="⬅️ Joriy vazifaga qaytish",
        callback_data=f"show_current_hw:{group_id}"
    )])

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("get_hw_file:"))
async def send_homework_file(callback: CallbackQuery):
    hw_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        hw = await session.get(Homework, hw_id)

    if not hw or not hw.file_id:
        await callback.answer("Fayl topilmadi.", show_alert=True)
        return

    from main import bot
    try:
        await bot.send_document(
            callback.from_user.id,
            hw.file_id,
            caption=f"📎 <b>{hw.title}</b> dars materiali",
        )
        await callback.answer("Fayl yuborildi!")
    except Exception:
        # Fayl rasm yoki audio bo'lishi mumkin
        try:
            await bot.send_photo(callback.from_user.id, hw.file_id, caption=f"📎 <b>{hw.title}</b>")
            await callback.answer("Rasm yuborildi!")
        except Exception:
            await callback.answer("Faylni yuklashda xatolik yuz berdi.", show_alert=True)
