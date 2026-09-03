import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import text
from backend.database import engine, Base, async_session
import backend.models  # Modellar ro'yxatdan o'tishi uchun
from backend.models import User, RoleEnum, LanguageEnum, CenterSetting


async def wipe_and_init_clean():
    print("=" * 60)
    print("🧹 BAZA 100% TOZALANMOQDA (FAQAT ADMIN 1435473812 QOLADI)...")
    print("=" * 60)

    # 1. Barcha jadvallarni o'chirish
    async with engine.begin() as conn:
        print("[1/3] Jadvallarni o'chirish (DROP SCHEMA public CASCADE)...")
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))

    # 2. Yangi bo'sh jadvallarni yaratish
    async with engine.begin() as conn:
        print("[2/3] Yangi bo'sh jadvallarni yaratish...")
        await conn.run_sync(Base.metadata.create_all)

    # 3. Faqat 1 ta Bosh Admin va Tizim Sozlamasini yaratish
    async with async_session() as session:
        print("[3/3] Bosh Admin va Markaz Sozlamasini kiritish...")
        
        # Center settings
        setting = CenterSetting(
            id=1,
            contact_phone="+998901234567",
            contact_username="english_center_admin",
            address={
                "uz": "Toshkent sh., Amir Temur ko'chasi, 12-uy",
                "ru": "г. Ташкент, ул. Амира Темура, д. 12",
                "en": "12 Amir Temur street, Tashkent"
            },
        )
        session.add(setting)

        # Single Admin 1435473812
        admin_user = User(
            id=1435473812,
            full_name="Bosh Admin",
            username=None,
            phone=None,
            role=RoleEnum.admin,
            language=LanguageEnum.uz,
            referral_code="ADMIN1435",
            is_active=True,
        )
        session.add(admin_user)
        await session.commit()

    print("=" * 60)
    print("✅ BAZA 100% TOZA HOLATDA TAYYOR BO'LDI!")
    print("   👤 Bosh Admin: 1435473812 (admin)")
    print("   📚 Kurslar: 0 ta (bo'sh)")
    print("   👥 Guruhlar: 0 ta (bo'sh)")
    print("   🎯 Testlar: 0 ta (bo'sh)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(wipe_and_init_clean())
