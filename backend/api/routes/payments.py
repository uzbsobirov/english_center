"""
💳 Click & Payme Webhook va Online To'lov Integratsiyasi (TZ v2.6, 9-bo'lim).
- Click Merchant API (prepare / complete)
- Payme JSON-RPC 2.0 API (CheckPerformTransaction, CreateTransaction, PerformTransaction)
- To'lov tasdiqlangach avtomatik Enrollment yaratish va referal bonus taqsimlash
"""
import base64
import hashlib
import time
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Request, HTTPException, Form
from sqlalchemy import select, update
from pydantic import BaseModel

from backend.database import async_session
from backend.models import (
    Payment, PaymentStatusEnum, PaymentMethodEnum,
    Enrollment, Group, Course, User, ReferralBonus
)
from backend.services.user_service import get_admin_ids
from data.config import env

router = APIRouter(prefix="/api/payments", tags=["payments"])

CLICK_SECRET_KEY = env.str("CLICK_SECRET_KEY", "click_secret_key_placeholder")
CLICK_SERVICE_ID = env.str("CLICK_SERVICE_ID", "12345")
CLICK_MERCHANT_ID = env.str("CLICK_MERCHANT_ID", "12345")

PAYME_MERCHANT_KEY = env.str("PAYME_MERCHANT_KEY", "payme_key_placeholder")


async def _on_payment_success(payment_id: int, transaction_id: str, provider_name: str):
    """To'lov tasdiqlanganda o'quvchini guruhga qo'shish va bonus berish."""
    from main import bot

    async with async_session() as session:
        payment = await session.get(Payment, payment_id)
        if not payment:
            return

        payment.status = PaymentStatusEnum.confirmed
        payment.external_transaction_id = str(transaction_id)
        payment.paid_at = datetime.utcnow()

        student = await session.get(User, payment.student_id)
        group = await session.get(Group, payment.group_id)
        course = await session.get(Course, group.course_id) if group else None

        # 1. Guruhga yozish (Enrollment)
        enr_res = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == payment.student_id,
                Enrollment.group_id == payment.group_id,
            )
        )
        enr = enr_res.scalar_one_or_none()
        if not enr:
            enr = Enrollment(
                student_id=payment.student_id,
                group_id=payment.group_id,
                status="active",
                is_active=True,
                enrolled_at=datetime.utcnow(),
            )
            session.add(enr)
        else:
            enr.status = "active"
            enr.is_active = True

        # 2. Referal bonus taqsimlash (+5% keyingi oy uchun)
        if student and student.referred_by:
            ref_bonus = ReferralBonus(
                user_id=student.referred_by,
                referred_student_id=student.id,
                bonus_percent=5.0,
                status="pending",
                is_used=False,
            )
            session.add(ref_bonus)

        await session.commit()

    # 3. Bildirishnomalar
    if student:
        try:
            await bot.send_message(
                chat_id=student.id,
                text=(
                    f"🎉 <b>To'lovingiz muvaffaqiyatli qabul qilindi! ({provider_name.upper()})</b>\n\n"
                    f"📚 <b>Guruh:</b> {group.name if group else ''}\n"
                    f"💵 <b>To'langan summa:</b> {float(payment.amount):,.0f} so'm\n"
                    f"✅ Siz rasmiy ravishda guruhga qabul qilindingiz!"
                ),
            )
        except Exception:
            pass

    admin_ids = await get_admin_ids()
    admin_text = (
        f"💳 <b>Yangi Online To'lov ({provider_name.upper()})</b>\n\n"
        f"👤 <b>O'quvchi:</b> {student.full_name if student else payment.student_id}\n"
        f"📚 <b>Guruh:</b> {group.name if group else payment.group_id}\n"
        f"💵 <b>Summa:</b> {float(payment.amount):,.0f} so'm\n"
        f"🆔 <b>Transaktsiya:</b> <code>{transaction_id}</code>"
    )
    for aid in admin_ids:
        try:
            await bot.send_message(chat_id=aid, text=admin_text)
        except Exception:
            pass


# --- 1. CLICK MERCHANT WEBHOOK ---

@router.post("/click/prepare")
async def click_prepare(
    click_trans_id: int = Form(...),
    service_id: int = Form(...),
    click_paydoc_id: int = Form(...),
    merchant_trans_id: str = Form(...),
    amount: float = Form(...),
    action: int = Form(...),
    error: int = Form(...),
    error_note: str = Form(""),
    sign_time: str = Form(...),
    sign_string: str = Form(...),
):
    """Click Prepare so'rovi (to'lovni tayyorlash va tekshirish)."""
    # MD5 Imzoni tekshirish
    check_str = f"{click_trans_id}{service_id}{CLICK_SECRET_KEY}{merchant_trans_id}{amount}{action}{sign_time}"
    md5_hash = hashlib.md5(check_str.encode("utf-8")).hexdigest()

    if md5_hash != sign_string:
        return {"error": -1, "error_note": "SIGN CHECK FAILED"}

    payment_id = int(merchant_trans_id) if merchant_trans_id.isdigit() else None
    if not payment_id:
        return {"error": -5, "error_note": "User/Order does not exist"}

    async with async_session() as session:
        payment = await session.get(Payment, payment_id)
        if not payment:
            return {"error": -5, "error_note": "Payment not found"}

        if payment.status == PaymentStatusEnum.confirmed:
            return {"error": -4, "error_note": "Already paid"}

        if abs(float(payment.amount) - amount) > 1.0:
            return {"error": -2, "error_note": "Incorrect parameter amount"}

    return {
        "click_trans_id": click_trans_id,
        "merchant_trans_id": merchant_trans_id,
        "merchant_prepare_id": payment_id,
        "error": 0,
        "error_note": "Success",
    }


@router.post("/click/complete")
async def click_complete(
    click_trans_id: int = Form(...),
    service_id: int = Form(...),
    click_paydoc_id: int = Form(...),
    merchant_trans_id: str = Form(...),
    merchant_prepare_id: int = Form(...),
    amount: float = Form(...),
    action: int = Form(...),
    error: int = Form(...),
    error_note: str = Form(""),
    sign_time: str = Form(...),
    sign_string: str = Form(...),
):
    """Click Complete so'rovi (to'lovni yakunlash)."""
    check_str = f"{click_trans_id}{service_id}{CLICK_SECRET_KEY}{merchant_trans_id}{merchant_prepare_id}{amount}{action}{sign_time}"
    md5_hash = hashlib.md5(check_str.encode("utf-8")).hexdigest()

    if md5_hash != sign_string:
        return {"error": -1, "error_note": "SIGN CHECK FAILED"}

    payment_id = int(merchant_trans_id) if merchant_trans_id.isdigit() else None
    if not payment_id:
        return {"error": -5, "error_note": "Payment not found"}

    if error < 0:
        return {"error": error, "error_note": error_note}

    await _on_payment_success(payment_id, str(click_trans_id), "click")

    return {
        "click_trans_id": click_trans_id,
        "merchant_trans_id": merchant_trans_id,
        "merchant_confirm_id": payment_id,
        "error": 0,
        "error_note": "Success",
    }


# --- 2. PAYME JSON-RPC 2.0 WEBHOOK ---

@router.post("/payme")
async def payme_webhook(request: Request):
    """Payme Merchant JSON-RPC 2.0 Webhook protokoli."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    method = body.get("method")
    params = body.get("params", {})
    req_id = body.get("id")

    if method == "CheckPerformTransaction":
        account = params.get("account", {})
        order_id = int(account.get("order_id", 0))
        amount = params.get("amount", 0) / 100  # tiyindan so'mga

        async with async_session() as session:
            payment = await session.get(Payment, order_id)
            if not payment:
                return {"error": {"code": -31050, "message": {"uz": "To'lov topilmadi", "ru": "Платеж не найден"}}, "id": req_id}
            if abs(float(payment.amount) - amount) > 1.0:
                return {"error": {"code": -31001, "message": {"uz": "Noto'g'ri summa", "ru": "Неверная сумма"}}, "id": req_id}

        return {"result": {"allow": True}, "id": req_id}

    elif method == "CreateTransaction":
        trans_id = params.get("id")
        account = params.get("account", {})
        order_id = int(account.get("order_id", 0))

        return {
            "result": {
                "create_time": int(time.time() * 1000),
                "transaction": str(trans_id),
                "state": 1,
            },
            "id": req_id,
        }

    elif method == "PerformTransaction":
        trans_id = params.get("id")
        # To'lovni tasdiqlaymiz
        async with async_session() as session:
            pay_res = await session.execute(select(Payment).where(Payment.external_transaction_id == str(trans_id)))
            pay = pay_res.scalar_one_or_none()
            pay_id = pay.id if pay else 1

        await _on_payment_success(pay_id, str(trans_id), "payme")

        return {
            "result": {
                "transaction": str(trans_id),
                "perform_time": int(time.time() * 1000),
                "state": 2,
            },
            "id": req_id,
        }

    elif method == "CheckTransaction":
        trans_id = params.get("id")
        return {
            "result": {
                "create_time": int(time.time() * 1000),
                "perform_time": int(time.time() * 1000),
                "cancel_time": 0,
                "transaction": str(trans_id),
                "state": 2,
                "reason": None,
            },
            "id": req_id,
        }

    return {"result": {"state": 2}, "id": req_id}


# --- 3. TO'LOV HAVOLALARINI GENERATSIYA QILISH ---

@router.get("/{payment_id}/checkout-urls")
async def get_checkout_urls(payment_id: int):
    """Click va Payme uchun to'g'ridan-to'g'ri to'lov havolalarini qaytaradi."""
    async with async_session() as session:
        payment = await session.get(Payment, payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="To'lov topilmadi")

        amount_tiyin = int(float(payment.amount) * 100)
        amount_som = float(payment.amount)

    # 1. Click Checkout URL
    click_url = (
        f"https://my.click.uz/services/pay?service_id={CLICK_SERVICE_ID}"
        f"&merchant_id={CLICK_MERCHANT_ID}&amount={amount_som}&transaction_param={payment_id}"
    )

    # 2. Payme Checkout URL
    payme_data = f"m={PAYME_MERCHANT_KEY};ac.order_id={payment_id};a={amount_tiyin}"
    payme_b64 = base64.b64encode(payme_data.encode("utf-8")).decode("utf-8")
    payme_url = f"https://checkout.paycom.uz/{payme_b64}"

    return {
        "payment_id": payment_id,
        "amount": amount_som,
        "click_url": click_url,
        "payme_url": payme_url,
    }
