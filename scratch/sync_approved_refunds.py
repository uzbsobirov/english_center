import asyncio
import sys
import os
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, update
from backend.database import async_session
from backend.models import Enrollment, Payment, Refund, EnrollmentStatusEnum, PaymentStatusEnum

async def sync_approved_refunds():
    async with async_session() as session:
        # Topamiz: status="approved" bo'lgan refundlar
        res = await session.execute(select(Refund).where(Refund.status == "approved"))
        refunds = res.scalars().all()
        print(f"Found {len(refunds)} approved refunds in DB.")

        for r in refunds:
            print(f"Syncing Refund ID={r.id}, student={r.student_id}, group={r.group_id}")
            # Deactivate enrollment
            enr_res = await session.execute(
                select(Enrollment).where(
                    Enrollment.student_id == r.student_id,
                    Enrollment.group_id == r.group_id,
                    Enrollment.is_active == True,
                )
            )
            for enr in enr_res.scalars().all():
                enr.status = EnrollmentStatusEnum.dropped
                enr.is_active = False
                enr.completed_at = datetime.utcnow()
                print(f"  -> Deactivated Enrollment ID={enr.id}")

            # Mark payment as refunded
            if r.payment_id:
                pay = await session.get(Payment, r.payment_id)
                if pay:
                    pay.status = PaymentStatusEnum.refunded
                    print(f"  -> Payment ID={pay.id} set to refunded")
            else:
                pay_res = await session.execute(
                    select(Payment).where(
                        Payment.student_id == r.student_id,
                        Payment.group_id == r.group_id,
                        Payment.status == PaymentStatusEnum.confirmed,
                    )
                )
                for p in pay_res.scalars().all():
                    p.status = PaymentStatusEnum.refunded
                    print(f"  -> Payment ID={p.id} set to refunded")

        await session.commit()
        print("[SUCCESS] All approved refunds synced with enrollments & payments!")

if __name__ == "__main__":
    asyncio.run(sync_approved_refunds())
