"""
DB ulanish sozlamalari.
PostgreSQL + SQLAlchemy (async) uchun asosiy fayl.
"""
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# 1. To'g'ridan-to'g'ri DATABASE_URL berilgan bo'lsa o'qiladi
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Agar yo'q bo'lsa, alohida DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME dan yig'iladi
if not DATABASE_URL:
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASS", "1234")
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "english_center")
    DATABASE_URL = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

engine = create_async_engine(DATABASE_URL, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Barcha modellar shu klassdan meros oladi."""
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency sifatida ishlatiladi."""
    async with async_session() as session:
        yield session