import asyncio
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from sqlalchemy import text, select
from backend.database import engine, Base, async_session
from backend.models import (
    User, RoleEnum, LanguageEnum, LevelEnum, CourseTypeEnum,
    Course, Group, Test, CenterSetting
)
from init_db import seed_center_settings, seed_courses_and_groups, seed_admins


async def clean_and_reseed():
    print("=" * 60)
    print("🧹 BAZANI TOZALASH (TESTLAR SAQLAB QOLINADI)...")
    print("=" * 60)

    # Testlar va savollardan tashqari barcha jadvallar
    preserve_tables = {"tests", "questions"}
    
    # Barcha mavjud modellar jadvallari
    all_table_names = [t.name for t in Base.metadata.sorted_tables if t.name not in preserve_tables]

    async with engine.begin() as conn:
        # 1. tests jadvalidagi teacher_id FK larni bo'shatamiz
        await conn.execute(text("UPDATE tests SET teacher_id = NULL;"))

        # 2. Barcha belgilangan jadvallarni tozalaymiz (TRUNCATE CASCADE)
        for tbl in reversed(all_table_names):
            try:
                print(f"  [-] Tozalanmoqda: {tbl}...")
                await conn.execute(text(f"TRUNCATE TABLE {tbl} RESTART IDENTITY CASCADE;"))
            except Exception as e:
                print(f"  [!] O'tkazib yuborildi ({tbl}): {e}")

    print("\n" * 1)
    print("=" * 60)
    print("🌱 YANGI MA'LUMOTLAR BILAN SEED QILISH...")
    print("=" * 60)

    async with async_session() as session:
        # 1. Markaz sozlamalari
        print("  [+] Markaz sozlamalari tiklanmoqda...")
        await seed_center_settings(session)

        # 2. Adminlar va o'qituvchilar
        print("  [+] Adminlar yaratilmoqda...")
        await seed_admins(session)

        # 3. Kurslar va guruhlar
        print("  [+] Kurslar va guruhlar yaratilmoqda...")
        await seed_courses_and_groups(session)

        await session.commit()

    async with async_session() as session:
        t_count = (await session.execute(text("SELECT COUNT(*) FROM tests"))).scalar()
        c_count = (await session.execute(text("SELECT COUNT(*) FROM courses"))).scalar()
        g_count = (await session.execute(text("SELECT COUNT(*) FROM groups"))).scalar()
        u_count = (await session.execute(text("SELECT COUNT(*) FROM users"))).scalar()

    print("=" * 60)
    print(f"✅ BAZA TO'LIQ TOZALANDI VA TIKLANDI!")
    print(f"   📝 Saqlab qolingan testlar: {t_count} ta")
    print(f"   📚 Yangi kurslar: {c_count} ta")
    print(f"   👥 Yangi guruhlar: {g_count} ta")
    print(f"   👤 Boshlang'ich foydalanuvchilar: {u_count} ta")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(clean_and_reseed())
