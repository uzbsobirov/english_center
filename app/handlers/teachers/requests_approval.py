"""
👥 Guruh o'zgartirish va 💰 To'lov qaytarish (Refund) so'rovlarini tasdiqlash handlerlari (TZ v2.6, 7.6 va 9.3).
"""
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select, update

from backend.database import async_session
from backend.models import (
    GroupChangeRequest, Refund, Enrollment, Group, Payment, PaymentStatusEnum, User
)
from backend.services.user_service import is_admin_or_manager

router = Router()


# --- 👥 GURUHNI O'ZGARTIRISHNI TASDIQLASH / RAD ETISH ---

@router.callback_query(F.data.startswith("grp_chg_acc:"))
async def approve_group_change(callback: CallbackQuery):
    req_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    from main import bot

    async with async_session() as session:
        req = await session.get(GroupChangeRequest, req_id)
        if not req:
            await callback.answer("So'rov topilmadi.", show_alert=True)
            return

        if req.status != "pending":
            await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
            return

        target_grp = await session.get(Group, req.target_group_id)
        cur_grp = await session.get(Group, req.current_group_id)

        req.status = "approved"
        req.approved_by = user_id
        req.processed_at = datetime.utcnow()

        # O'quvchining faol enrollmentini yangilaymiz
        enr_res = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == req.student_id,
                Enrollment.group_id == req.current_group_id,
                Enrollment.is_active == True,
            )
        )
        enr = enr_res.scalar_one_or_none()
        if enr:
            enr.group_id = req.target_group_id

        await session.commit()

    # Admin xabarini yangilaymiz
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.reply(
            f"✅ <b>Guruh o'zgartirish tasdiqlandi!</b>\n"
            f"O'quvchi: <code>{req.student_id}</code>\n"
            f"Yangi guruh: <b>{target_grp.name if target_grp else req.target_group_id}</b>\n"
            f"Tasdiqladi: {callback.from_user.full_name}"
        )
    except Exception:
        pass

    # O'quvchiga xabar jo'natamiz
    try:
        await bot.send_message(
            chat_id=req.student_id,
            text=(
                f"🎉 <b>Guruhni o'zgartirish so'rovingiz tasdiqlandi!</b>\n\n"
                f"Siz muvaffaqiyatli <b>{target_grp.name if target_grp else ''}</b> guruhiga o'tkazildingiz.\n"
                f"📅 Dars jadvali va xona ma'lumotlarini «📅 Jadvalim» bo'limida ko'rishingiz mumkin."
            ),
        )
    except Exception:
        pass

    await callback.answer("Muvaffaqiyatli tasdiqlandi!")


@router.callback_query(F.data.startswith("grp_chg_rej:"))
async def reject_group_change(callback: CallbackQuery):
    req_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    from main import bot

    async with async_session() as session:
        req = await session.get(GroupChangeRequest, req_id)
        if not req:
            await callback.answer("So'rov topilmadi.", show_alert=True)
            return

        if req.status != "pending":
            await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
            return

        req.status = "rejected"
        req.approved_by = user_id
        req.processed_at = datetime.utcnow()
        await session.commit()

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.reply(f"❌ Guruh o'zgartirish rad etildi ({callback.from_user.full_name}).")
    except Exception:
        pass

    try:
        await bot.send_message(
            chat_id=req.student_id,
            text="❌ <b>Guruhni o'zgartirish so'rovingiz ma'muriyat tomonidan rad etildi.</b>\n"
                 "Batafsil ma'lumot uchun o'qituvchingiz yoki adminga murojaat qiling.",
        )
    except Exception:
        pass

    await callback.answer("Rad etildi.")


# --- 💰 QAYTARISH (REFUND) TASDIQLASH / RAD ETISH ---

@router.callback_query(F.data.startswith("ref_adm_acc:"))
async def approve_refund(callback: CallbackQuery):
    ref_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    from main import bot

    async with async_session() as session:
        ref = await session.get(Refund, ref_id)
        if not ref:
            await callback.answer("Refund so'rovi topilmadi.", show_alert=True)
            return

        if ref.status != "pending":
            await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
            return

        ref.status = "approved"
        ref.approved_by = user_id
        ref.final_amount = ref.calculated_amount
        ref.processed_at = datetime.utcnow()

        # O'quvchini guruhdan chiqaramiz
        enr_res = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == ref.student_id,
                Enrollment.group_id == ref.group_id,
                Enrollment.is_active == True,
            )
        )
        enr = enr_res.scalar_one_or_none()
        if enr:
            enr.status = EnrollmentStatusEnum.dropped
            enr.is_active = False
            enr.completed_at = datetime.utcnow()

        if ref.payment_id:
            pay = await session.get(Payment, ref.payment_id)
            if pay:
                pay.status = PaymentStatusEnum.refunded
        else:
            await session.execute(
                update(Payment)
                .where(
                    Payment.student_id == ref.student_id,
                    Payment.group_id == ref.group_id,
                    Payment.status == PaymentStatusEnum.confirmed,
                )
                .values(status=PaymentStatusEnum.refunded)
            )

        await session.commit()
        calculated_amount = float(ref.calculated_amount)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.reply(
            f"✅ <b>Qaytarish (Refund) tasdiqlandi!</b>\n"
            f"Summa: <b>{calculated_amount:,.0f} so'm</b>\n"
            f"Tasdiqladi: {callback.from_user.full_name}"
        )
    except Exception:
        pass

    try:
        await bot.send_message(
            chat_id=ref.student_id,
            text=(
                f"💰 <b>To'lovni qaytarish (Refund) tasdiqlandi!</b>\n\n"
                f"💵 Qaytarilgan summa: <b>{calculated_amount:,.0f} so'm</b>\n"
                f"Mablag'ni markaz ma'muriyatidan qabul qilib olishingiz mumkin."
            ),
        )
    except Exception:
        pass

    await callback.answer("Refund muvaffaqiyatli tasdiqlandi!")


@router.callback_query(F.data.startswith("ref_adm_rej:"))
async def reject_refund(callback: CallbackQuery):
    ref_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    from main import bot

    async with async_session() as session:
        ref = await session.get(Refund, ref_id)
        if not ref:
            await callback.answer("Refund so'rovi topilmadi.", show_alert=True)
            return

        if ref.status != "pending":
            await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
            return

        ref.status = "rejected"
        ref.approved_by = user_id
        ref.processed_at = datetime.utcnow()
        await session.commit()

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.reply(f"❌ Qaytarish rad etildi ({callback.from_user.full_name}).")
    except Exception:
        pass

    try:
        await bot.send_message(
            chat_id=ref.student_id,
            text="❌ <b>To'lovni qaytarish so'rovingiz ma'muriyat tomonidan rad etildi.</b>\n"
                 "Batafsil ma'lumot uchun admin bilan bog'laning.",
        )
    except Exception:
        pass

    await callback.answer("Rad etildi.")
