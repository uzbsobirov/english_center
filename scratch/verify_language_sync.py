import sys
import os
import asyncio
import json

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath("."))

from backend.database import async_session
from backend.models import User, RoleEnum, LanguageEnum, CenterSetting
from app.utils.i18n_manager import UserManager
from app.keyboards.admin_menu import admin_menu_keyboard, ADMIN_MENU_TEXTS_BY_LANG
from aiogram.types import User as TgUser
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

async def main():
    print("🚀 Starting Unified Language & Admin Panel Verification...")

    test_user_id = 9999888877

    async with async_session() as session:
        # Create test user
        user = await session.get(User, test_user_id)
        if not user:
            user = User(
                id=test_user_id,
                full_name="Lang Test User",
                username="lang_test_user",
                role=RoleEnum.admin,
                language=LanguageEnum.uz,
            )
            session.add(user)
            await session.commit()
        else:
            user.language = LanguageEnum.uz
            await session.commit()

    print("1. Initial user language in DB: uz")

    # Verify i18n UserManager get_locale
    storage = MemoryStorage()
    key = StorageKey(bot_id=12345, chat_id=test_user_id, user_id=test_user_id)
    fsm = FSMContext(storage=storage, key=key)
    tg_user = TgUser(id=test_user_id, is_bot=False, first_name="Lang", username="lang_test_user")

    mgr = UserManager()
    locale = await mgr.get_locale(tg_user, fsm)
    assert locale == "uz", f"Expected 'uz', got {locale}"
    print("✅ Initial get_locale returned 'uz'")

    # Simulate WebApp calling API / DB update to "en"
    async with async_session() as session:
        db_user = await session.get(User, test_user_id)
        db_user.language = LanguageEnum.en
        await session.commit()

    print("2. WebApp changed language to 'en' in DB")

    # Even if FSM had old data 'uz', UserManager should prioritize DB!
    await fsm.update_data(language="uz")
    locale2 = await mgr.get_locale(tg_user, fsm)
    assert locale2 == "en", f"Expected 'en' from DB, got {locale2}"
    fsm_data = await fsm.get_data()
    assert fsm_data.get("language") == "en", f"Expected FSM synced to 'en', got {fsm_data.get('language')}"
    print("✅ get_locale correctly prioritized DB and synchronized FSM to 'en'")

    # Test Admin Menu Keyboards in UZ, RU, EN
    kb_uz = admin_menu_keyboard(user_id=test_user_id, user_name="Admin", lang="uz", is_admin=True)
    kb_en = admin_menu_keyboard(user_id=test_user_id, user_name="Admin", lang="en", is_admin=True)
    kb_ru = admin_menu_keyboard(user_id=test_user_id, user_name="Admin", lang="ru", is_admin=True)

    uz_texts = [b.text for row in kb_uz.keyboard for b in row]
    en_texts = [b.text for row in kb_en.keyboard for b in row]
    ru_texts = [b.text for row in kb_ru.keyboard for b in row]

    assert "📊 Admin Dashboard" in uz_texts
    assert "📊 Admin Dashboard" in en_texts
    assert "📊 Панель админа" in ru_texts
    assert "◀️ Asosiy menyu" in uz_texts
    assert "◀️ Main Menu" in en_texts
    assert "◀️ Главное меню" in ru_texts
    print("✅ Admin Menu Keyboards generated correctly in UZ, EN, and RU!")

    # Test CenterSettings welcome message persistence
    async with async_session() as session:
        setting = await session.get(CenterSetting, 1)
        if not setting:
            setting = CenterSetting(id=1)
            session.add(setting)

        setting.welcome_message = {
            "uz": "Test UZ Xush kelibsiz",
            "ru": "Test RU Приветствие",
            "en": "Test EN Welcome",
        }
        await session.commit()

    async with async_session() as session:
        verified_setting = await session.get(CenterSetting, 1)
        assert verified_setting.welcome_message["uz"] == "Test UZ Xush kelibsiz"
        assert verified_setting.welcome_message["ru"] == "Test RU Приветствие"
        assert verified_setting.welcome_message["en"] == "Test EN Welcome"
    print("✅ CenterSettings 3-language welcome message persisted and verified!")

    # Cleanup test user
    async with async_session() as session:
        u = await session.get(User, test_user_id)
        if u:
            await session.delete(u)
            await session.commit()

    print("🎉 All Unified Language & Admin Panel tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
