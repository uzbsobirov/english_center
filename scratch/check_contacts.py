import asyncio
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from backend.database import async_session
from backend.models import CenterSetting

async def check_settings():
    async with async_session() as session:
        res = await session.execute(select(CenterSetting))
        settings = res.scalars().all()
        print(f"Total CenterSettings in DB: {len(settings)}")
        for s in settings:
            print(f"- Phone: {s.contact_phone} | Admin: @{s.contact_username} | Address: {s.address}")

if __name__ == "__main__":
    asyncio.run(check_settings())
