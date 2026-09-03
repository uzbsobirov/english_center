import asyncio
from backend.database import async_session
from backend.models import User, Group, Enrollment, Payment

async def inspect():
    async with async_session() as session:
        from sqlalchemy import select
        users = (await session.execute(select(User))).scalars().all()
        print("--- USERS ---")
        for u in users:
            print(f"User: id={u.id}, name={u.full_name}, role={u.role}, is_active={u.is_active}")

        groups = (await session.execute(select(Group))).scalars().all()
        print("\n--- GROUPS ---")
        for g in groups:
            print(f"Group: id={g.id}, name={g.name}, max_students={g.max_students}, is_active={g.is_active}")

        enrs = (await session.execute(select(Enrollment))).scalars().all()
        print("\n--- ENROLLMENTS ---")
        for e in enrs:
            print(f"Enrollment: id={e.id}, student_id={e.student_id}, group_id={e.group_id}, status={e.status}, is_active={e.is_active}")

        pays = (await session.execute(select(Payment))).scalars().all()
        print("\n--- PAYMENTS ---")
        for p in pays:
            print(f"Payment: id={p.id}, student_id={p.student_id}, group_id={p.group_id}, amount={p.amount}, status={p.status}")

if __name__ == "__main__":
    asyncio.run(inspect())
