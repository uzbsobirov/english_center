import asyncio
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from backend.database import async_session
from backend.models import SupportChat

async def inspect_support():
    async with async_session() as session:
        res = await session.execute(select(SupportChat))
        chats = res.scalars().all()
        print(f"Total SupportChats: {len(chats)}")
        for c in chats:
            print(f"- ID: {c.id} | student: {c.student_id} | admin: {c.admin_id} | status: {c.status} | reason: {c.closed_reason} | last_msg: {c.last_message_at}")

if __name__ == "__main__":
    asyncio.run(inspect_support())
