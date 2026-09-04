import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from dotenv import load_dotenv

# Loyiha tub papkasini import yo'liga qo'shamiz (backend/models.py topilishi uchun)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

load_dotenv()

from backend.database import Base
from backend import models  # noqa: F401  -- barcha modellar shu yerda ro'yxatga olinadi

config = context.config

# Migratsiya uchun SINXRON (psycopg2) URL ishlatamiz, asyncpg emas
db_url = os.getenv("DATABASE_URL_SYNC")
if not db_url:
    async_url = os.getenv("DATABASE_URL")
    if async_url:
        db_url = async_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    else:
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASS", "1234")
        db_host = os.getenv("DB_HOST", "127.0.0.1")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "english_center")
        db_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()