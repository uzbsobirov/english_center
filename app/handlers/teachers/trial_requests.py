"""
O'qituvchi / Admin tomonidan free-dars so'rovini qabul qilish yoki rad etish.
TZ v2.6, 7.1.1: 'Birinchi bosgan g'olib' mexanizmi - SQL darajasidagi ATOMIK UPDATE orqali
amalga oshiriladi (race condition oldini olinadi).
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import update, select

from backend.database import async_session
from backend.models import FreeTrialRequest, FreeTrialStatusEnum, User, RoleEnum, Group, Course, TestResult, Test

router = Router()


@router.callback_query(F.data.startswith("trial_accept:"))
async def accept_trial(callback: CallbackQuery):
    trial_id = int(callback.data.split(":")[1])
    teacher_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(
            update(FreeTrialRequest)
            .where(
                FreeTrialRequest.id == trial_id,
                FreeTrialRequest.status == FreeTrialStatusEnum.pending,
            )
            .values(status=FreeTrialStatusEnum.invited, teacher_id=teacher_id)
        )
        await session.commit()

        won = result.rowcount > 0

        if not won:
            await callback.answer(
                "Kechirasiz, bu so'rov allaqachon ko'rib chiqilgan yoki boshqa admin/o'qituvchi tomonidan qabul qilingan.",
                show_alert=True,
            )
            return

        trial = await session.get(FreeTrialRequest, trial_id)
        if trial and not trial.group_id and trial.test_result_id:
            test_res = await session.get(TestResult, trial.test_result_id)
            if test_res:
                test_obj = await session.get(Test, test_res.test_id)
                if test_obj:
                    grp_res = await session.execute(
                        select(Group)
                        .join(Course, Group.course_id == Course.id)
                        .where(
                            Course.level == test_obj.level,
                            Group.is_active == True,
                        ).order_by((Group.teacher_id == teacher_id).desc()).limit(1)
                    )
                    assigned_grp = grp_res.scalars().first()
                    if assigned_grp:
                        trial.group_id = assigned_grp.id
                        await session.commit()

        student = await session.get(User, trial.student_id) if trial else None
        teacher = await session.get(User, teacher_id)

    from main import bot

    if student:
        student_username_str = f"@{student.username}" if student.username else "Mavjud emas"
        student_link = f"<a href='tg://user?id={student.id}'>{student.full_name}</a>"
        phone_str = student.phone or "Kiritilmagan"

        teacher_card_text = (
            f"✅ <b>Siz free-dars so'rovini QABUL QILDINGIZ!</b>\n\n"
            f"👤 <b>O'quvchi:</b> {student_link}\n"
            f"📱 <b>Telefon:</b> {phone_str}\n"
            f"🌐 <b>Username:</b> {student_username_str}\n"
            f"🆔 <b>Telegram ID:</b> <code>{student.id}</code>\n\n"
            f"<i>Iltimos, o'quvchi bilan bog'lanib, bepul sinov darsi vaqti va joyini kelishib oling.</i>"
        )
        teacher_buttons = []
        if student.username:
            teacher_buttons.append([InlineKeyboardButton(text="💬 O'quvchiga yozish", url=f"https://t.me/{student.username}")])
        else:
            teacher_buttons.append([InlineKeyboardButton(text="👤 O'quvchi Profilini Ochish", url=f"tg://user?id={student.id}")])

        # Dars kuni davomatini belgilash tugmalari (TZ 6.2)
        teacher_buttons.append([
            InlineKeyboardButton(text="🟢 Darsga Keldi", callback_data=f"trial_att_yes:{trial_id}"),
            InlineKeyboardButton(text="🔴 Kelmadi", callback_data=f"trial_att_no:{trial_id}"),
        ])

        await callback.message.edit_text(
            teacher_card_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=teacher_buttons),
        )

        # O'quvchiga xabar
        teacher_name = teacher.full_name if teacher else callback.from_user.full_name
        teacher_username = f"@{teacher.username}" if teacher and teacher.username else ""
        teacher_link = f"<a href='tg://user?id={teacher_id}'>{teacher_name}</a>"

        student_msg = (
            f"🎉 <b>Tabriklaymiz! Bepul sinov darsi so'rovingiz qabul qilindi.</b>\n\n"
            f"👨‍🏫 <b>Sizning o'qituvchingiz:</b> {teacher_link} {teacher_username}\n\n"
            f"O'qituvchingiz tez orada siz bilan bog'lanib, bepul sinov darsi vaqti va joyini ma'lum qiladi."
        )
        student_buttons = []
        if teacher and teacher.username:
            student_buttons.append([InlineKeyboardButton(text="👨‍🏫 O'qituvchiga yozish", url=f"https://t.me/{teacher.username}")])
        else:
            student_buttons.append([InlineKeyboardButton(text="👨‍🏫 O'qituvchi Profilini Ochish", url=f"tg://user?id={teacher_id}")])

        try:
            await bot.send_message(
                student.id,
                student_msg,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=student_buttons),
            )
        except Exception:
            pass
    else:
        await callback.message.edit_text("✅ Siz ushbu so'rovni qabul qildingiz!")

    await callback.answer("Muvaffaqiyatli qabul qilindi!")


# --- 🟢 FREE DARS DAVOMATI VA O'QUVCHI BAHOLASHI (TZ 6.2) ---

@router.callback_query(F.data.startswith("trial_att_yes:"))
async def mark_trial_attended(callback: CallbackQuery):
    trial_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        trial = await session.get(FreeTrialRequest, trial_id)
        if not trial:
            await callback.answer("So'rov topilmadi.", show_alert=True)
            return

        trial.status = FreeTrialStatusEnum.attended
        await session.commit()
        student_id = trial.student_id

    from main import bot

    await callback.message.reply("✅ <b>O'quvchi bepul darsda qatnashdi deb belgilandi!</b>")

    # O'quvchiga 1-5 yulduzli baholash yuboramiz
    rating_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐ 1", callback_data=f"rate_tr:{trial_id}:1"),
            InlineKeyboardButton(text="⭐ 2", callback_data=f"rate_tr:{trial_id}:2"),
            InlineKeyboardButton(text="⭐ 3", callback_data=f"rate_tr:{trial_id}:3"),
            InlineKeyboardButton(text="⭐ 4", callback_data=f"rate_tr:{trial_id}:4"),
            InlineKeyboardButton(text="⭐ 5", callback_data=f"rate_tr:{trial_id}:5"),
        ]
    ])

    try:
        await bot.send_message(
            chat_id=student_id,
            text=(
                "🌟 <b>Bugungi bepul sinov darsimiz sizga yoqdimi?</b>\n\n"
                "Iltimos, dars va o'qituvchini 1 dan 5 gacha baholang:"
            ),
            reply_markup=rating_kb,
        )
    except Exception:
        pass

    await callback.answer("Davomat belgilandi!")


@router.callback_query(F.data.startswith("trial_att_no:"))
async def mark_trial_not_attended(callback: CallbackQuery):
    trial_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        trial = await session.get(FreeTrialRequest, trial_id)
        if trial:
            trial.status = FreeTrialStatusEnum.declined
            await session.commit()
            student_id = trial.student_id

    from main import bot

    await callback.message.reply("❌ <b>O'quvchi darsga kelmadi deb belgilandi.</b>")

    try:
        await bot.send_message(
            chat_id=student_id,
            text=(
                "Bugungi bepul sinov darsimizda qatnasha olmadingiz.\n"
                "Keyingi bo'sh guruhlarga bemalol qayta yozilishingiz mumkin!"
            ),
        )
    except Exception:
        pass

    await callback.answer("Belgilandi.")


@router.callback_query(F.data.startswith("rate_tr:"))
async def student_submit_trial_rating(callback: CallbackQuery):
    parts = callback.data.split(":")
    trial_id = int(parts[1])
    stars = int(parts[2])

    async with async_session() as session:
        trial = await session.get(FreeTrialRequest, trial_id)
        if trial:
            trial.student_rating = stars
            await session.commit()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💳 Rasmiy guruhga to'lov qilish", callback_data="start_payment_flow"),
        ],
        [
            InlineKeyboardButton(text="❌ Yo'q, rahmat", callback_data="trial_no_enroll"),
        ]
    ])

    await callback.message.edit_text(
        f"⭐️ <b>Fikringiz uchun katta rahmat! ({stars}/5 yulduz)</b>\n\n"
        f"Guruhda o'qishni rasman davom ettirishni xohlaysizmi?",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == "trial_no_enroll")
async def trial_decline_enrollment(callback: CallbackQuery):
    await callback.message.edit_text(
        "Fikringiz uchun rahmat! Sizni kelgusida markazimizda ko'rishdan doim xursandmiz. 😊"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("trial_reject:"))
async def reject_trial(callback: CallbackQuery):
    trial_id = int(callback.data.split(":")[1])
    teacher_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(
            update(FreeTrialRequest)
            .where(
                FreeTrialRequest.id == trial_id,
                FreeTrialRequest.status == FreeTrialStatusEnum.pending,
            )
            .values(status=FreeTrialStatusEnum.declined, teacher_id=teacher_id)
        )
        await session.commit()

        won = result.rowcount > 0

        if not won:
            await callback.answer(
                "Kechirasiz, bu so'rov allaqachon ko'rib chiqilgan.",
                show_alert=True,
            )
            return

        trial = await session.get(FreeTrialRequest, trial_id)
        student = await session.get(User, trial.student_id) if trial else None

    from main import bot

    student_link = f"<a href='tg://user?id={student.id}'>{student.full_name}</a>" if student else "O'quvchi"
    await callback.message.edit_text(
        f"❌ <b>Free-dars so'rovi rad etildi.</b>\n\n"
        f"👤 <b>O'quvchi:</b> {student_link}\n"
        f"<i>Holat: Rad etildi</i>"
    )

    if student:
        try:
            await bot.send_message(
                student.id,
                "❌ <b>Afsuski, bepul sinov darsi so'rovingiz qabul qilinmadi.</b>\n\n"
                "Qo'shimcha ma'lumot olish yoki boshqa yo'nalishlar bo'yicha maslahat olish uchun ma'muriyat bilan bog'lanishingiz mumkin.",
            )
        except Exception:
            pass

    await callback.answer("So'rov rad etildi.")


# --- 🎯 KUTILAYOTGAN SINOV DARSLARI RO'YXATI (DAVOMAT) ---

@router.message(Command("trials", "trial_attendance"))
@router.message(F.text.in_({"🎯 Sinov darslari", "🎯 Sinov darslari davomati", "🎯 Free darslar"}))
@router.callback_query(F.data == "show_trial_attendance_list")
async def show_trial_attendance_list(event: Message | CallbackQuery):
    user_id = event.from_user.id
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user and user.role in (RoleEnum.admin, RoleEnum.manager):
            query = select(FreeTrialRequest, User).join(User, FreeTrialRequest.student_id == User.id).where(
                FreeTrialRequest.status == FreeTrialStatusEnum.invited
            ).order_by(FreeTrialRequest.created_at.desc())
        else:
            query = select(FreeTrialRequest, User).join(User, FreeTrialRequest.student_id == User.id).where(
                FreeTrialRequest.status == FreeTrialStatusEnum.invited,
                FreeTrialRequest.teacher_id == user_id,
            ).order_by(FreeTrialRequest.created_at.desc())
        
        res = await session.execute(query)
        trials = res.all()

    if not trials:
        msg = "🎯 <b>Hozirda kutilayotgan sinov darslari mavjud emas.</b>\n\nBarcha qabul qilingan o'quvchilar davomati belgilangan."
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(msg)
            await event.answer()
        else:
            await event.answer(msg)
        return

    buttons = []
    for trial, student in trials:
        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {student.full_name} (ID: #{trial.id})",
                callback_data=f"view_trial_att:{trial.id}"
            )
        ])

    text = f"🎯 <b>Kutilayotgan Sinov Darslari ({len(trials)} ta)</b>\n\nDavomatini belgilash uchun o'quvchini tanlang:"
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        await event.answer()
    else:
        await event.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("view_trial_att:"))
async def view_trial_for_attendance(callback: CallbackQuery):
    trial_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        trial = await session.get(FreeTrialRequest, trial_id)
        if not trial:
            await callback.answer("So'rov topilmadi.", show_alert=True)
            return
        student = await session.get(User, trial.student_id)
        group = await session.get(Group, trial.group_id) if trial.group_id else None

    student_name = student.full_name if student else f"User #{trial.student_id}"
    phone_str = student.phone if student and student.phone else "Kiritilmagan"
    group_name = group.name if group else "Umumiy sinov darsi"

    text = (
        f"🎯 <b>Sinov Darsi Davomati</b>\n\n"
        f"👤 <b>O'quvchi:</b> <b>{student_name}</b>\n"
        f"📱 <b>Telefon:</b> {phone_str}\n"
        f"👥 <b>Guruh:</b> {group_name}\n"
        f"📌 <b>Holat:</b> Taklif qilingan (Dars kutilmoqda)\n\n"
        f"<i>O'quvchi bugungi darsga keldimi?</i>"
    )
    buttons = [
        [
            InlineKeyboardButton(text="🟢 Darsga Keldi", callback_data=f"trial_att_yes:{trial.id}"),
            InlineKeyboardButton(text="🔴 Kelmadi", callback_data=f"trial_att_no:{trial.id}"),
        ],
        [
            InlineKeyboardButton(text="◀️ Ro'yxatga qaytish", callback_data="show_trial_attendance_list"),
        ]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()