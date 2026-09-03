import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from backend.database import async_session
from backend.models import User

async def list_users():
    async with async_session() as session:
        res = await session.execute(select(User))
        users = res.scalars().all()
        print(f"Total users in DB: {len(users)}")
        for u in users:
            print(f"- ID: {u.id} | Name: {u.full_name} | Role: {u.role} | Phone: {u.phone}")

if __name__ == "__main__":
    asyncio.run(list_users())
