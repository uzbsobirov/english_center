import sys
import asyncio

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.database import async_session
from backend.models import User, Course, Group, Enrollment, Payment

async def inspect():
    async with async_session() as s:
        from sqlalchemy import select
        cs = (await s.execute(select(Course))).scalars().all()
        gs = (await s.execute(select(Group))).scalars().all()
        us = (await s.execute(select(User))).scalars().all()
        
        print("Courses count:", len(cs))
        for c in cs:
            t = c.title.get("uz") if isinstance(c.title, dict) else str(c.title)
            print(f"  Course ID {c.id}: {t} ({c.price:,.0f} UZS)")

        print("\nGroups count:", len(gs))
        for g in gs:
            print(f"  Group ID {g.id}: {g.name} | Teacher ID: {g.teacher_id} | Max: {g.max_students}")

        print("\nUsers count:", len(us))
        for u in us:
            print(f"  User ID {u.id}: {u.full_name} | Role: {u.role}")

if __name__ == "__main__":
    asyncio.run(inspect())
