import asyncio
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, User as TgUser, Chat
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey

from app.handlers.users.settings import submit_refund_reason, SettingsFSM, ALL_NAV_BUTTONS
from app.keyboards.admin_menu import ADMIN_PANEL_BUTTON_TEXTS

async def test_flow():
    storage = MemoryStorage()
    key = StorageKey(bot_id=123, chat_id=456, user_id=456)
    state = FSMContext(storage=storage, key=key)
    
    # Set initial state & data
    await state.set_state(SettingsFSM.refund_reason)
    await state.update_data(
        payment_id=1,
        group_id=1,
        calculated_refund=150000,
        paid_amount=200000,
        attended_count=1,
    )
    
    # 1. Test clicking '👑 Admin Panel'
    msg1 = MagicMock(spec=Message)
    msg1.text = "👑 Admin Panel"
    msg1.from_user = TgUser(id=456, is_bot=False, first_name="Test", username="test")
    msg1.chat = Chat(id=456, type="private")
    msg1.answer = AsyncMock()
    
    i18n = MagicMock()
    i18n.locale = "uz"
    i18n.get = MagicMock(side_effect=lambda k: k)
    
    await submit_refund_reason(msg1, state, i18n)
    
    current_state = await state.get_state()
    assert current_state is None, f"Expected state to be cleared on Admin Panel click, got {current_state}"
    print("Test 1 Passed: Admin Panel cleared state and did not submit refund!")
    
    # 2. Test clicking menu button 'Profilim'
    await state.set_state(SettingsFSM.refund_reason)
    msg2 = MagicMock(spec=Message)
    msg2.text = "👤 Profilim"
    msg2.from_user = TgUser(id=456, is_bot=False, first_name="Test", username="test")
    msg2.chat = Chat(id=456, type="private")
    msg2.answer = AsyncMock()
    
    await submit_refund_reason(msg2, state, i18n)
    current_state = await state.get_state()
    assert current_state is None, f"Expected state to be cleared on menu button click, got {current_state}"
    print("Test 2 Passed: Profilim cleared state and did not submit refund!")
    
    # 3. Test typing too short text 'ok'
    await state.set_state(SettingsFSM.refund_reason)
    msg3 = MagicMock(spec=Message)
    msg3.text = "ok"
    msg3.from_user = TgUser(id=456, is_bot=False, first_name="Test", username="test")
    msg3.chat = Chat(id=456, type="private")
    msg3.answer = AsyncMock()
    
    await submit_refund_reason(msg3, state, i18n)
    current_state = await state.get_state()
    assert current_state == SettingsFSM.refund_reason.state, f"Expected state to remain refund_reason, got {current_state}"
    msg3.answer.assert_called_once()
    print("Test 3 Passed: Short text 'ok' prompted for longer explanation without submitting!")

if __name__ == "__main__":
    asyncio.run(test_flow())
