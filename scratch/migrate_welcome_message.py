import sys
import os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from sqlalchemy import text
from backend.database import engine

async def migrate():
    async with engine.begin() as conn:
        try:
            # SQLite / Postgres check
            await conn.execute(text("ALTER TABLE center_settings ADD COLUMN welcome_message JSON"))
            print("Successfully added 'welcome_message' column to center_settings!")
        except Exception as e:
            print(f"Column might already exist or note: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
