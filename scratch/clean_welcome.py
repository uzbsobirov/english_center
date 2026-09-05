import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from backend.database import async_session
from backend.models import CenterSetting

async def clean():
    async with async_session() as s:
        setting = await s.get(CenterSetting, 1)
        if setting:
            setting.welcome_message = None
            await s.commit()
            print("Successfully cleared welcome_message in CenterSetting!")

if __name__ == "__main__":
    asyncio.run(clean())
