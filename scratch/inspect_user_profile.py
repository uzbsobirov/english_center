import asyncio
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from backend.database import async_session
from backend.models import Enrollment, Payment, User, Group, Refund

async def inspect():
    async with async_session() as session:
        enr_res = await session.execute(select(Enrollment))
        enrollments = enr_res.scalars().all()
        print("=== ENROLLMENTS ===")
        for e in enrollments:
            print(f"ID={e.id} | student_id={e.student_id} | group_id={e.group_id} | status={e.status} | is_active={e.is_active}")

        pay_res = await session.execute(select(Payment))
        payments = pay_res.scalars().all()
        print("\n=== PAYMENTS ===")
        for p in payments:
            print(f"ID={p.id} | student_id={p.student_id} | group_id={p.group_id} | amount={p.amount} | status={p.status}")

        ref_res = await session.execute(select(Refund))
        refunds = ref_res.scalars().all()
        print("\n=== REFUNDS ===")
        for r in refunds:
            print(f"ID={r.id} | student_id={r.student_id} | group_id={r.group_id} | status={r.status} | amount={r.calculated_amount}")

if __name__ == "__main__":
    asyncio.run(inspect())
