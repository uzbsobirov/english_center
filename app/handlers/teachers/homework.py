"""
Uy vazifasi qo'shish (TZ v2.6, 7.4-bo'lim).
- O'qituvchi guruhga uy vazifasi qo'shadi (sarlavha, izoh, fayl)
- Guruhdagi barcha o'quvchilarga darhol bildirishnoma ketadi
"""
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from backend.database import async_session
from backend.models import Group, Enrollment, User, Homework
from backend.services.user_service import is_teacher
from app.state.homework import HomeworkState

router = Router()


@router.message(Command("add_homework"))
async def start_add_homework(message: Message, state: FSMContext):
    if not await is_teacher(message.from_user.id):
        await message.answer("Bu buyruq faqat o'qituvchilar uchun.")
        return

    async with async_session() as session:
        result = await session.execute(
            select(Group).where(Group.teacher_id == message.from_user.id, Group.is_active == True)
        )
        groups = result.scalars().all()

    if not groups:
        await message.answer("Sizga biriktirilgan faol guruh topilmadi.")
        return

    buttons = [
        [InlineKeyboardButton(text=g.name, callback_data=f"hw_group:{g.id}")]
        for g in groups
    ]
    await message.answer("📋 Uy vazifasi qo'shmoqchi bo'lgan guruhingizni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("hw_group:"))
async def homework_group_selected(callback: CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        group = await session.get(Group, group_id)

    await state.update_data(group_id=group_id, group_name=group.name)
    await state.set_state(HomeworkState.entering_title)
    await callback.message.edit_text(
        f"Guruh: <b>{group.name}</b>\n\n"
        f"Uy vazifasi sarlavhasini kiriting (masalan: <i>Unit 4 — Vocabulary & Reading</i>):"
    )
    await callback.answer()


@router.message(HomeworkState.entering_title, F.text)
async def homework_title_entered(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(HomeworkState.entering_description)
    await message.answer("📝 Vazifa tavsifini / ko'rsatmalarini kiriting (yoki /skip deb yozing):")


@router.message(HomeworkState.entering_description)
async def homework_description_entered(message: Message, state: FSMContext):
    desc = message.text.strip() if message.text and message.text != "/skip" else None
    await state.update_data(description=desc)
    await state.set_state(HomeworkState.uploading_file)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏩ Faylsiz saqlash", callback_data="hw_skip_file")]
    ])
    await message.answer("📎 Fayl / Rasm / Audio biriktiring yoki 'Faylsiz saqlash'ni bosing:", reply_markup=keyboard)


@router.callback_query(HomeworkState.uploading_file, F.data == "hw_skip_file")
@router.message(HomeworkState.uploading_file)
async def homework_file_saved(event: Message | CallbackQuery, state: FSMContext):
    file_id = None
    if isinstance(event, Message):
        if event.document:
            file_id = event.document.file_id
        elif event.photo:
            file_id = event.photo[-1].file_id
        elif event.audio:
            file_id = event.audio.file_id
        elif event.voice:
            file_id = event.voice.file_id

    data = await state.get_data()
    teacher_id = event.from_user.id
    group_id = data["group_id"]
    title = data["title"]
    desc = data.get("description")

    # Due date: standart 2 kundan keyin
    due_date = datetime.utcnow() + timedelta(days=2)

    async with async_session() as session:
        hw = Homework(
            group_id=group_id,
            teacher_id=teacher_id,
            title=title,
            description=desc,
            file_id=file_id,
            due_at=due_date,
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
        f"{'📝 ' + desc if desc else ''}\n\n"
        f"⏳ Muddat: <b>{due_date.strftime('%d.%m.%Y %H:%M')}</b>"
    )
    for s in students:
        try:
            if file_id and isinstance(event, Message) and event.document:
                await bot.send_document(s.id, file_id, caption=notify_text)
            elif file_id and isinstance(event, Message) and event.photo:
                await bot.send_photo(s.id, file_id, caption=notify_text)
            else:
                await bot.send_message(s.id, notify_text)
        except Exception:
            continue

    await state.clear()
    msg = f"✅ <b>Uy vazifasi muvaffaqiyatli saqlandi va barcha o'quvchilarga yuborildi!</b>"
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(msg)
        await event.answer()
    else:
        await event.answer(msg)
