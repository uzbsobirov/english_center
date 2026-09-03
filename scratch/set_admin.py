import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from backend.database import async_session
from backend.models import User, RoleEnum, Test
from sqlalchemy import update, select

from sqlalchemy import delete

async def main():
    async with async_session() as session:
        await session.execute(delete(User))
        await session.commit()
        print("[OK] Users jadvali to'liq tozalandi! Bot endi registratsiya so'raydi.")

if __name__ == "__main__":
    asyncio.run(main())
