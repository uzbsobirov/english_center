"""
Uy vazifasi qo'shish (TZ v2.6, 7.4-bo'lim & 13 Avtomatik Eslatmalar).
- O'qituvchi/Admin guruhga uy vazifasi qo'shadi (sarlavha, izoh, fayl)
- Guruhdagi barcha o'quvchilarga darhol bildirishnoma ketadi
- Muddat belgilanadi
"""
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from backend.database import async_session
from backend.models import Group, Enrollment, User, RoleEnum, Homework
from app.state.homework import HomeworkState

router = Router()


async def _is_teacher_or_admin(telegram_id: int) -> bool:
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        return user is not None and user.role in (RoleEnum.teacher, RoleEnum.admin, RoleEnum.manager)


async def _get_groups_for_homework(user_id: int):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user and user.role in (RoleEnum.admin, RoleEnum.manager):
            result = await session.execute(
                select(Group).where(Group.is_active == True)
            )
        else:
            result = await session.execute(
                select(Group).where(Group.teacher_id == user_id, Group.is_active == True)
            )
        return result.scalars().all()


@router.message(Command("add_homework"))
@router.message(F.text.in_({"📋 Uy vazifasi qo'shish", "📋 Uy vazifasi yuklash", "Uy vazifasi qo'shish", "Homework"}))
async def start_add_homework(message: Message, state: FSMContext):
    if not await _is_teacher_or_admin(message.from_user.id):
        await message.answer("Bu buyruq faqat o'qituvchilar va adminlar uchun.")
        return

    groups = await _get_groups_for_homework(message.from_user.id)
    if not groups:
        await message.answer("Sizga biriktirilgan faol guruh topilmadi.")
        return

    buttons = [
        [InlineKeyboardButton(text=f"👥 {g.name}", callback_data=f"hw_group:{g.id}")]
        for g in groups
    ]
    await message.answer(
        "📋 <b>Yangi Uy Vazifasi Qo'shish</b>\n\nGuruhni tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("hw_group:"))
async def homework_group_selected(callback: CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        group = await session.get(Group, group_id)

    if not group:
        await callback.answer("Guruh topilmadi", show_alert=True)
        return

    await state.update_data(group_id=group_id, group_name=group.name)
    await state.set_state(HomeworkState.entering_title)
    await callback.message.edit_text(
        f"👥 Guruh: <b>{group.name}</b>\n\n"
        f"Uy vazifasi sarlavhasini kiriting (masalan: <i>Unit 4 — Vocabulary & Reading Practice</i>):"
    )
    await callback.answer()


@router.message(HomeworkState.entering_title, F.text)
async def homework_title_entered(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(HomeworkState.entering_description)
    await message.answer(
        "📝 Vazifa tavsifini / ko'rsatmalarini kiriting (yoki o'tkazib yuborish uchun <code>/skip</code> deb yozing):"
    )


@router.message(HomeworkState.entering_description)
async def homework_description_entered(message: Message, state: FSMContext):
    desc = message.text.strip() if message.text and message.text != "/skip" else None
    await state.update_data(description=desc)
    await state.set_state(HomeworkState.uploading_file)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏩ Faylsiz saqlash va yuborish", callback_data="hw_skip_file")]
    ])
    await message.answer(
        "📎 <b>Vazifaga tegishli faylni yuboring</b> (PDF, rasm, audio, video yoki hujjat):\n"
        "Yoki fayl kerak bo'lmasa, quyidagi tugmani bosing:",
        reply_markup=keyboard,
    )


@router.callback_query(HomeworkState.uploading_file, F.data == "hw_skip_file")
@router.message(HomeworkState.uploading_file)
async def homework_file_saved(event: Message | CallbackQuery, state: FSMContext):
    file_id = None
    file_type = None

    if isinstance(event, Message):
        if event.document:
            file_id = event.document.file_id
            file_type = "document"
        elif event.photo:
            file_id = event.photo[-1].file_id
            file_type = "photo"
        elif event.audio:
            file_id = event.audio.file_id
            file_type = "audio"
        elif event.video:
            file_id = event.video.file_id
            file_type = "video"
        elif event.voice:
            file_id = event.voice.file_id
            file_type = "voice"

    data = await state.get_data()
    teacher_id = event.from_user.id
    group_id = data["group_id"]
    title = data["title"]
    desc = data.get("description")

    # Due date: keyingi darsgacha (standart 2 kun)
    due_date = datetime.utcnow() + timedelta(days=2)

    async with async_session() as session:
        hw = Homework(
            group_id=group_id,
            teacher_id=teacher_id,
            title=title,
            description=desc,
            file_id=file_id,
            due_at=due_date,
            lesson_date=datetime.utcnow().date(),
        )
        session.add(hw)
        await session.commit()

        # Guruhdagi barcha o'quvchilarga bildirishnoma yuborish (TZ 7.4 & 13)
        enrolled_res = await session.execute(
            select(User)
            .join(Enrollment, Enrollment.student_id == User.id)
            .where(Enrollment.group_id == group_id, Enrollment.is_active == True)
        )
        students = enrolled_res.scalars().all()

    from main import bot
    notify_text = (
        f"📋 <b>Yangi uy vazifasi qo'shildi!</b>\n\n"
        f"👥 Guruh: <b>{data['group_name']}</b>\n"
        f"📌 <b>{title}</b>\n"
        f"{'📝 ' + desc + chr(10) if desc else ''}\n"
        f"⏳ <b>Topshirish muddati:</b> {due_date.strftime('%d.%m.%Y %H:%M')}"
    )

    for s in students:
        try:
            if file_id:
                if file_type == "document":
                    await bot.send_document(s.id, file_id, caption=notify_text)
                elif file_type == "photo":
                    await bot.send_photo(s.id, file_id, caption=notify_text)
                elif file_type == "audio":
                    await bot.send_audio(s.id, file_id, caption=notify_text)
                elif file_type == "video":
                    await bot.send_video(s.id, file_id, caption=notify_text)
                elif file_type == "voice":
                    await bot.send_voice(s.id, file_id, caption=notify_text)
                else:
                    await bot.send_message(s.id, notify_text)
            else:
                await bot.send_message(s.id, notify_text)
        except Exception:
            continue

    await state.clear()
    success_msg = f"✅ <b>Uy vazifasi muvaffaqiyatli saqlandi va guruhdagi barcha o'quvchilarga ({len(students)} ta) tarqatildi!</b>"
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(success_msg)
        await event.answer()
    else:
        await event.answer(success_msg)
