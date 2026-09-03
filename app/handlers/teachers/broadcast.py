"""
📢 Telegram Bot Admin Broadcast Tizimi (TZ v2.6, 8.1).
Adminlarga matn, rasm, video, hujjat, @postbot tugmali postlar yoki forward xabarlarni
barcha o'quvchilarga, o'qituvchilarga yoki tanlangan guruhlarga yuborish imkonini beradi.
"""
import asyncio
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
)
from sqlalchemy import select

from backend.database import async_session
from backend.models import User, RoleEnum, Enrollment, Group, Course
from backend.services.user_service import is_admin_or_manager

router = Router()


class BroadcastFSM(StatesGroup):
    choosing_target = State()
    waiting_for_content = State()
    waiting_for_button = State()
    confirm_send = State()


BROADCAST_BUTTON_TEXTS = {
    "📢 Xabar yuborish (Broadcast)",
    "📢 Xabar yuborish",
    "📢 Broadcast",
    "📢 Рассылка",
}


@router.message(F.text.in_(BROADCAST_BUTTON_TEXTS))
async def start_broadcast(message: Message, state: FSMContext):
    if not await is_admin_or_manager(message.from_user.id):
        await message.answer("Bu funksiya faqat adminlar uchun.")
        return

    await state.clear()
    await state.set_state(BroadcastFSM.choosing_target)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Barcha foydalanuvchilar (Barchaga)", callback_data="bc_target:all"),
        ],
        [
            InlineKeyboardButton(text="🎓 Faqat o'quvchilar", callback_data="bc_target:students"),
            InlineKeyboardButton(text="👨‍🏫 Faqat o'qituvchilar", callback_data="bc_target:teachers"),
        ],
        [
            InlineKeyboardButton(text="🎯 IELTS kursdagilar", callback_data="bc_target:IELTS"),
            InlineKeyboardButton(text="🎯 CEFR kursdagilar", callback_data="bc_target:CEFR"),
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="bc_cancel"),
        ]
    ])

    await message.answer(
        "📢 <b>Ommaviy Xabarnoma (Broadcast)</b>\n\n"
        "Xabaringizni kimlarga yubormoqchisiz? Auditoriyani tanlang:",
        reply_markup=keyboard,
    )


@router.callback_query(BroadcastFSM.choosing_target, F.data.startswith("bc_target:"))
async def target_selected(callback: CallbackQuery, state: FSMContext):
    target = callback.data.split(":")[1]
    await state.update_data(target=target)
    await state.set_state(BroadcastFSM.waiting_for_content)

    target_labels = {
        "all": "👥 Barcha foydalanuvchilar",
        "students": "🎓 Faqat o'quvchilar",
        "teachers": "👨‍🏫 Faqat o'qituvchilar",
        "IELTS": "🎯 IELTS kursdagilar",
        "CEFR": "🎯 CEFR kursdagilar",
    }
    label = target_labels.get(target, target)

    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="bc_cancel")]
    ])

    await callback.message.edit_text(
        f"📢 <b>Auditoriya:</b> {label}\n\n"
        f"Endi yubormoqchi bo'lgan xabaringizni jo'nating:\n"
        f"• <i>Oddiy matn (HTML formatlash bilan)</i>\n"
        f"• <i>Rasm yoki Video (izohi bilan)</i>\n"
        f"• <i>Hujjat / PDF fayl</i>\n"
        f"• <i>@postbot orqali tugmali postlar</i>\n"
        f"• <i>Istalgan kanaldagi postni Forward qilib yuborishingiz ham mumkin!</i>",
        reply_markup=cancel_kb,
    )
    await callback.answer()


@router.message(BroadcastFSM.waiting_for_content)
async def receive_broadcast_content(message: Message, state: FSMContext):
    data = await state.get_data()
    target = data.get("target", "all")

    is_forwarded = bool(
        getattr(message, "forward_origin", None)
        or getattr(message, "forward_from", None)
        or getattr(message, "forward_from_chat", None)
    )

    has_original_markup = message.reply_markup is not None
    original_markup_dict = message.reply_markup.model_dump() if has_original_markup else None

    # Xabar turi va ma'lumotlarini saqlaymiz
    content_info = {
        "message_id": message.message_id,
        "chat_id": message.chat.id,
        "content_type": message.content_type,
        "is_forward": is_forwarded,
        "has_original_markup": has_original_markup,
        "original_markup": original_markup_dict,
        "has_custom_button": False,
        "button_text": None,
        "button_url": None,
        "send_mode": "copy", # 'copy' yoki 'forward'
    }
    await state.update_data(content_info=content_info)
    await state.set_state(BroadcastFSM.confirm_send)

    buttons = []
    if is_forwarded:
        buttons.append([
            InlineKeyboardButton(text="⏩ Asl nusxada Forward qilish", callback_data="bc_send_mode:forward"),
            InlineKeyboardButton(text="📋 Bot nomidan Copy qilish", callback_data="bc_send_mode:copy"),
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="🚀 Xabarni Hozir Yuborish", callback_data="bc_send_now"),
        ])

    if not has_original_markup:
        buttons.append([
            InlineKeyboardButton(text="🔗 Inline Tugma Qo'shish", callback_data="bc_add_btn"),
        ])

    buttons.append([
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="bc_cancel"),
    ])

    extra_note = ""
    if has_original_markup:
        extra_note = "\n\n<i>(@postbot tugmalari aniqlandi va barchasi saqlab qolinadi ✅)</i>"
    elif is_forwarded:
        extra_note = "\n\n<i>(Forward qilingan post aniqlandi)</i>"

    await message.reply(
        f"✅ <b>Xabar qabul qilindi!</b>{extra_note}\n\n"
        f"Quyidagi harakatlardan birini tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(BroadcastFSM.confirm_send, F.data.startswith("bc_send_mode:"))
async def change_send_mode(callback: CallbackQuery, state: FSMContext):
    mode = callback.data.split(":")[1]
    data = await state.get_data()
    content_info = data.get("content_info", {})
    content_info["send_mode"] = mode
    await state.update_data(content_info=content_info)

    mode_label = "⏩ Asl nusxada Forward" if mode == "forward" else "📋 Bot nomidan Copy"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🚀 Tasdiqlash va Yuborish ({mode_label})", callback_data="bc_send_now")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="bc_cancel")],
    ])

    await callback.message.edit_text(
        f"✅ <b>Tanlangan usul:</b> {mode_label}\n\n"
        f"Xabarnomani barcha foydalanuvchilarga yuborishga tayyormisiz?",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(BroadcastFSM.confirm_send, F.data == "bc_add_btn")
async def ask_for_button(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastFSM.waiting_for_button)
    await callback.message.edit_text(
        "🔗 <b>Tugma qo'shish formati:</b>\n\n"
        "Tugma matni va havolasini <code>|</code> belgisi bilan yozib yuboring:\n\n"
        "<i>Namuna:</i>\n"
        "<code>Batafsil ma'lumot | https://t.me/alphacenter</code>\n"
        "<code>Free Darsga Yozilish | https://t.me/alphalcbot</code>"
    )
    await callback.answer()


@router.message(BroadcastFSM.waiting_for_button, F.text)
async def process_custom_button(message: Message, state: FSMContext):
    text = message.text.strip()
    if "|" not in text:
        await message.answer(
            "⚠️ Noto'g'ri format! Iltimos, <code>Tugma nomi | https://havola...</code> formatida yozing."
        )
        return

    parts = text.split("|", 1)
    btn_text = parts[0].strip()
    btn_url = parts[1].strip()

    if not btn_url.startswith("http://") and not btn_url.startswith("https://") and not btn_url.startswith("tg://"):
        btn_url = f"https://{btn_url}"

    data = await state.get_data()
    content_info = data.get("content_info", {})
    content_info["has_custom_button"] = True
    content_info["button_text"] = btn_text
    content_info["button_url"] = btn_url
    await state.update_data(content_info=content_info)
    await state.set_state(BroadcastFSM.confirm_send)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_text, url=btn_url)],
        [InlineKeyboardButton(text="🚀 Xabarni Hozir Yuborish", callback_data="bc_send_now")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="bc_cancel")],
    ])

    await message.answer(
        f"✅ <b>Tugma biriktirildi:</b> <code>[{btn_text}]({btn_url})</code>\n\n"
        f"Yuborishga tayyormisiz?",
        reply_markup=keyboard,
    )


@router.callback_query(BroadcastFSM.confirm_send, F.data == "bc_send_now")
async def execute_broadcast(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    target = data.get("target", "all")
    content_info = data.get("content_info", {})
    await state.clear()

    await callback.message.edit_text("⏳ <b>Xabarnoma yuborilmoqda... Iltimos kuting.</b>")

    # Qabul qiluvchilar ro'yxatini olamiz
    async with async_session() as session:
        if target == "students":
            res = await session.execute(select(User.id).where(User.role == RoleEnum.student, User.is_active == True))
        elif target == "teachers":
            res = await session.execute(select(User.id).where(User.role == RoleEnum.teacher, User.is_active == True))
        elif target in ("IELTS", "CEFR"):
            res = await session.execute(
                select(User.id.distinct())
                .join(Enrollment, User.id == Enrollment.student_id)
                .join(Group, Enrollment.group_id == Group.id)
                .join(Course, Group.course_id == Course.id)
                .where(Course.type == target, Enrollment.is_active == True)
            )
        else:
            res = await session.execute(select(User.id).where(User.is_active == True))

        recipient_ids = list(res.scalars().all())

    from main import bot

    # Reply markup (custom button yoki @postbot original markup)
    reply_markup = None
    if content_info.get("has_custom_button") and content_info.get("button_text") and content_info.get("button_url"):
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=content_info["button_text"], url=content_info["button_url"])]
        ])
    elif content_info.get("has_original_markup") and content_info.get("original_markup"):
        try:
            reply_markup = InlineKeyboardMarkup(**content_info["original_markup"])
        except Exception:
            pass

    send_mode = content_info.get("send_mode", "copy")
    from_chat_id = content_info["chat_id"]
    msg_id = content_info["message_id"]

    sent_count = 0
    fail_count = 0

    for uid in recipient_ids:
        try:
            if send_mode == "forward":
                await bot.forward_message(
                    chat_id=uid,
                    from_chat_id=from_chat_id,
                    message_id=msg_id,
                )
            else:
                if reply_markup:
                    await bot.copy_message(
                        chat_id=uid,
                        from_chat_id=from_chat_id,
                        message_id=msg_id,
                        reply_markup=reply_markup,
                    )
                else:
                    await bot.copy_message(
                        chat_id=uid,
                        from_chat_id=from_chat_id,
                        message_id=msg_id,
                    )
            sent_count += 1
            await asyncio.sleep(0.04)  # Rate limit himoyasi (30 msg/sec)
        except Exception:
            fail_count += 1

    await callback.message.edit_text(
        f"🎉 <b>Xabarnoma muvaffaqiyatli yakunlandi!</b>\n\n"
        f"📊 <b>Jami mo'ljallangan:</b> {len(recipient_ids)} ta\n"
        f"✅ <b>Yetkazildi:</b> {sent_count} ta\n"
        f"⚠️ <b>Yetib bormadi (bloklagan):</b> {fail_count} ta"
    )
    await callback.answer()


@router.callback_query(F.data == "bc_cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Xabarnoma yuborish bekor qilindi.")
    await callback.answer()
