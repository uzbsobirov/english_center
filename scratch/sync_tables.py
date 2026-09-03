import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import engine, Base
import backend.models

async def sync():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables synchronized successfully!")

if __name__ == "__main__":
    asyncio.run(sync())
