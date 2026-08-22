from aiogram import Router, F
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram_i18n import I18nContext

from backend.database import async_session
from backend.models import User

from app.state.registration import Registration
from app.keyboards.language import language_keyboard, LANGUAGE_BUTTONS
from app.keyboards.contact import phone_keyboard
from app.keyboards.main_menu import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, i18n: I18nContext):
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)

    if user is not None:
        # Oldin ro'yxatdan o'tgan foydalanuvchi - to'g'ridan-to'g'ri asosiy menyu
        await state.clear()
        await message.answer(
            i18n.get("welcome-back", name=user.full_name),
            reply_markup=main_menu_keyboard(i18n),
        )
        return

    # Yangi foydalanuvchi - registratsiyani boshlaymiz
    await state.set_state(Registration.choosing_language)
    await message.answer(
        i18n.get("choose-language"),
        reply_markup=language_keyboard(),
    )


@router.message(Registration.choosing_language, F.text.in_(LANGUAGE_BUTTONS.keys()))
async def language_chosen(message: Message, state: FSMContext, i18n: I18nContext):
    lang = LANGUAGE_BUTTONS[message.text]

    # Tilni FSM ichida saqlaymiz va i18n contextni shu tilga o'tkazamiz
    await i18n.set_locale(lang, state=state, event_from_user=message.from_user)

    await state.set_state(Registration.entering_name)
    await message.answer(i18n.get("ask-name"))


@router.message(Registration.choosing_language)
async def language_invalid(message: Message, i18n: I18nContext):
    # Foydalanuvchi ro'yxatdan tashqari matn yozib yuborsa
    await message.answer(
        i18n.get("choose-language"),
        reply_markup=language_keyboard(),
    )


@router.message(Registration.entering_name, F.text)
async def name_entered(message: Message, state: FSMContext, i18n: I18nContext):
    await state.update_data(full_name=message.text.strip())
    await state.set_state(Registration.entering_phone)
    await message.answer(
        i18n.get("ask-phone"),
        reply_markup=phone_keyboard(i18n),
    )


@router.message(Registration.entering_phone, F.contact)
async def phone_shared(message: Message, state: FSMContext, i18n: I18nContext):
    # Faqat o'zining raqamini yuborganini tekshiramiz
    if message.contact.user_id != message.from_user.id:
        await message.answer(i18n.get("invalid-phone"))
        return

    data = await state.get_data()
    full_name = data.get("full_name", message.from_user.full_name)
    language = data.get("language", "uz")

    async with async_session() as session:
        user = User(
            id=message.from_user.id,
            full_name=full_name,
            username=message.from_user.username,
            phone=message.contact.phone_number,
            language=language,
        )
        session.add(user)
        await session.commit()

    await state.clear()
    await message.answer(
        i18n.get("registration-done"),
        reply_markup=main_menu_keyboard(i18n),
    )


@router.message(Registration.entering_phone)
async def phone_invalid(message: Message, i18n: I18nContext):
    # Foydalanuvchi tugma o'rniga matn yozib yuborsa
    await message.answer(i18n.get("invalid-phone"))