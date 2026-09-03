import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import hashlib
from datetime import datetime
from sqlalchemy import select
from backend.database import async_session
from backend.models import (
    User, RoleEnum, LanguageEnum, Course, Group, Enrollment,
    Payment, PaymentStatusEnum, PaymentMethodEnum, ReferralBonus, LevelEnum
)
from backend.api.routes.payments import click_prepare, click_complete, CLICK_SECRET_KEY

async def run_webhook_tests():
    print("--- [TEST] Running Click & Payme Webhook Test Suite ---")
    async with async_session() as session:
        # Pre-cleanup
        test_uids = [666111222, 666333444]
        for tbl in [ReferralBonus, Payment, Enrollment, Group]:
            q = select(tbl)
            if hasattr(tbl, "student_id"):
                q = q.where(tbl.student_id.in_(test_uids))
            elif hasattr(tbl, "user_id"):
                q = q.where(tbl.user_id.in_(test_uids))
            elif hasattr(tbl, "teacher_id"):
                q = q.where(tbl.teacher_id.in_(test_uids))
            res = await session.execute(q)
            for item in res.scalars().all():
                await session.delete(item)
        await session.commit()
        existing_users = await session.execute(select(User).where(User.id.in_(test_uids)))
        for u in existing_users.scalars().all():
            await session.delete(u)
        await session.commit()

        # 1. Setup Referrer & Student
        referrer = User(
            id=666333444,
            full_name="Referrer Friend",
            username="referrer_friend",
            role=RoleEnum.student,
            language=LanguageEnum.uz,
        )
        student = User(
            id=666111222,
            full_name="New Student",
            username="new_student",
            phone="+998909998877",
            role=RoleEnum.student,
            referred_by=referrer.id,
            language=LanguageEnum.uz,
        )
        session.add_all([referrer, student])
        await session.commit()

        # Course & Group
        course = Course(
            title={"uz": "General English", "ru": "Общий английский", "en": "General English"},
            description={"uz": "Desc", "ru": "Описание", "en": "Desc"},
            type="General",
            level=LevelEnum.B1,
            duration_months=3,
            lessons_per_week=3,
            price=550000,
            price_per_lesson=45000,
            is_active=True,
        )
        session.add(course)
        await session.commit()
        await session.refresh(course)

        grp = Group(
            course_id=course.id,
            teacher_id=referrer.id,
            name="General-B1-Afternoon",
            schedule=[{"day": 2, "time": "15:00"}],
            is_active=True,
        )
        session.add(grp)
        await session.commit()
        await session.refresh(grp)

        # Pending payment
        pay = Payment(
            student_id=student.id,
            group_id=grp.id,
            amount=550000,
            method=PaymentMethodEnum.click,
            status=PaymentStatusEnum.pending,
        )
        session.add(pay)
        await session.commit()
        await session.refresh(pay)

        payment_id = pay.id
        print(f"[OK] Pending Payment #{payment_id} created for {pay.amount} so'm.")

    # 2. Test Click Prepare
    click_trans_id = 998877
    service_id = 12345
    sign_time = "2026-08-30 14:00:00"
    amount = 550000.0

    check_str = f"{click_trans_id}{service_id}{CLICK_SECRET_KEY}{payment_id}{amount}{0}{sign_time}"
    sign_string = hashlib.md5(check_str.encode("utf-8")).hexdigest()

    prep_res = await click_prepare(
        click_trans_id=click_trans_id,
        service_id=service_id,
        click_paydoc_id=123,
        merchant_trans_id=str(payment_id),
        amount=amount,
        action=0,
        error=0,
        error_note="",
        sign_time=sign_time,
        sign_string=sign_string,
    )
    assert prep_res["error"] == 0, f"Click Prepare failed: {prep_res}"
    print(f"[OK] Click Prepare verified: merchant_prepare_id={prep_res['merchant_prepare_id']}")

    # 3. Test Click Complete
    comp_check_str = f"{click_trans_id}{service_id}{CLICK_SECRET_KEY}{payment_id}{payment_id}{amount}{1}{sign_time}"
    comp_sign_string = hashlib.md5(comp_check_str.encode("utf-8")).hexdigest()

    comp_res = await click_complete(
        click_trans_id=click_trans_id,
        service_id=service_id,
        click_paydoc_id=123,
        merchant_trans_id=str(payment_id),
        merchant_prepare_id=payment_id,
        amount=amount,
        action=1,
        error=0,
        error_note="",
        sign_time=sign_time,
        sign_string=comp_sign_string,
    )
    assert comp_res["error"] == 0, f"Click Complete failed: {comp_res}"
    print(f"[OK] Click Complete verified: merchant_confirm_id={comp_res['merchant_confirm_id']}")

    # 4. Verify in DB
    async with async_session() as session:
        updated_pay = await session.get(Payment, payment_id)
        assert updated_pay.status == PaymentStatusEnum.confirmed
        assert updated_pay.external_transaction_id == str(click_trans_id)

        # Check Enrollment created
        enr_res = await session.execute(
            select(Enrollment).where(
                Enrollment.student_id == student.id,
                Enrollment.group_id == grp.id,
                Enrollment.is_active == True,
            )
        )
        enr = enr_res.scalar_one_or_none()
        assert enr is not None
        print(f"[OK] Student successfully enrolled in group: Enrollment ID={enr.id}")

        # Check ReferralBonus created for referrer
        bonus_res = await session.execute(
            select(ReferralBonus).where(ReferralBonus.user_id == referrer.id)
        )
        bonus = bonus_res.scalar_one_or_none()
        assert bonus is not None
        assert float(bonus.bonus_percent) == 5.0
        print(f"[OK] Referral +5% discount bonus awarded to Referrer ({referrer.id})")

        # Cleanup
        await session.delete(bonus)
        await session.delete(updated_pay)
        await session.delete(enr)
        await session.commit()

        await session.delete(grp)
        await session.commit()

        await session.delete(course)
        await session.delete(student)
        await session.delete(referrer)
        await session.commit()
        print("[OK] Test database cleaned up.")
        print("--- [ALL WEBHOOK TESTS PASSED] ---")

if __name__ == "__main__":
    asyncio.run(run_webhook_tests())
