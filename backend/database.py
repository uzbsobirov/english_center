"""
DB ulanish sozlamalari.
PostgreSQL + SQLAlchemy (async) uchun asosiy fayl.
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# .env dan o'qiladi, masalan:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/english_center
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:1234@localhost:5432/english_center",
)

engine = create_async_engine(DATABASE_URL, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Barcha modellar shu klassdan meros oladi."""
    pass


async def get_session() -> AsyncSession:
    """FastAPI dependency sifatida ishlatiladi."""
    async with async_session() as session:
        yield session