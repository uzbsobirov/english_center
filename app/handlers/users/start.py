from aiogram import Router, F
from aiogram.filters.command import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram_i18n import I18nContext
from sqlalchemy import select

from backend.database import async_session
from backend.models import User, LanguageEnum, RoleEnum

from app.state.registration import Registration
from app.keyboards.language import language_keyboard, LANGUAGE_BUTTONS
from app.keyboards.contact import phone_keyboard
from app.keyboards.main_menu import main_menu_keyboard
from backend.services.user_service import is_admin_or_manager, is_teacher

router = Router()


@router.message(CommandStart())
async def start(message: Message, command: CommandObject, state: FSMContext, i18n: I18nContext):
    if not message.from_user:
        return

    async with async_session() as session:
        user = await session.get(User, message.from_user.id)

    if user is not None:
        # Oldin ro'yxatdan o'tgan foydalanuvchi - to'g'ridan-to'g'ri asosiy menyu
        # Telegram ma'lumotlarini yangilab qo'yamiz
        async with async_session() as session:
            db_user = await session.get(User, message.from_user.id)
            if db_user:
                updated = False
                if db_user.username != message.from_user.username:
                    db_user.username = message.from_user.username
                    updated = True
                if message.from_user.full_name and db_user.full_name in ("Bosh Admin", "Foydalanuvchi", None, ""):
                    db_user.full_name = message.from_user.full_name
                    updated = True
                if updated:
                    await session.commit()
                    user = db_user

        await state.clear()
        is_admin = await is_admin_or_manager(user.id) or await is_teacher(user.id)
        await message.answer(
            i18n.get("welcome-back", name=user.full_name),
            reply_markup=main_menu_keyboard(
                i18n,
                user_id=message.from_user.id,
                user_name=user.full_name or message.from_user.full_name,
                username=message.from_user.username,
                is_admin=is_admin,
            ),
        )
        return

    # Referal parametrini tekshiramiz
    referred_by_id = None
    if command.args:
        ref_arg = command.args.strip()
        async with async_session() as session:
            # referral_code orqali izlaymiz
            res = await session.execute(
                select(User).where(User.referral_code == ref_arg)
            )
            referrer = res.scalars().first()
            if not referrer and ref_arg.startswith("REF") and ref_arg[3:].isdigit():
                referrer = await session.get(User, int(ref_arg[3:]))
            elif not referrer and ref_arg.isdigit():
                referrer = await session.get(User, int(ref_arg))

            if referrer and referrer.id != message.from_user.id:
                referred_by_id = referrer.id

    # Yangi foydalanuvchi - registratsiyani boshlaymiz
    await state.set_state(Registration.choosing_language)
    if referred_by_id:
        await state.update_data(referred_by=referred_by_id)

    await message.answer(
        i18n.get("choose-language"),
        reply_markup=language_keyboard(),
    )


@router.message(Registration.choosing_language, F.text.in_(LANGUAGE_BUTTONS.keys()))
async def language_chosen(message: Message, state: FSMContext, i18n: I18nContext):
    if not message.text or not message.from_user:
        return

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
    if not message.text:
        return

    await state.update_data(full_name=message.text.strip())
    await state.set_state(Registration.entering_phone)
    await message.answer(
        i18n.get("ask-phone"),
        reply_markup=phone_keyboard(i18n),
    )


@router.message(Registration.entering_phone, F.contact)
@router.message(Registration.entering_phone, F.text)
async def phone_shared(message: Message, state: FSMContext, i18n: I18nContext):
    new_phone = None
    if message.contact:
        # 1. Forward qilingan kontaktlarni tekshiramiz va rad etamiz
        is_forwarded = bool(
            getattr(message, "forward_origin", None)
            or getattr(message, "forward_from", None)
            or getattr(message, "forward_from_chat", None)
        )
        if is_forwarded:
            await message.answer(
                "⚠️ <b>Forward qilingan kontaktlar qabul qilinmaydi!</b>\n\n"
                "Iltimos, pastdagi <b>«📱 Raqamni yuborish»</b> tugmasini bosing.",
                reply_markup=phone_keyboard(i18n),
            )
            return

        # 2. Faqat o'zining Telegram akkauntiga tegishli raqam ekanligini tekshiramiz (agar Telegram user_id yuborgan bo'lsa)
        if message.contact.user_id and message.contact.user_id != message.from_user.id:
            await message.answer(
                "⚠️ <b>Xatolik!</b> Siz boshqa shaxsning kontaktini yubordingiz.\n\n"
                "Iltimos, faqat pastdagi <b>«📱 Raqamni yuborish»</b> tugmasi orqali <b>o'zingizning</b> raqamingizni yuboring!",
                reply_markup=phone_keyboard(i18n),
            )
            return
        new_phone = message.contact.phone_number
    elif message.text:
        import re
        phone_match = re.search(r"(\+?[0-9]{9,15})", message.text.replace(" ", "").replace("-", ""))
        if phone_match:
            new_phone = phone_match.group(1)

    if not new_phone:
        await message.answer(
            "⚠️ <b>Noto'g'ri telefon raqami.</b>\n\n"
            "Iltimos, pastdagi <b>«📱 Raqamni yuborish»</b> tugmasini bosing yoki <code>+998901234567</code> formatida yozing:",
            reply_markup=phone_keyboard(i18n),
        )
        return

    # Telefon raqamini xalqaro formatga keltirish (+998...)
    if not new_phone.startswith("+"):
        if len(new_phone) == 12 and new_phone.startswith("998"):
            new_phone = "+" + new_phone
        elif len(new_phone) == 9:
            new_phone = "+998" + new_phone
        else:
            new_phone = "+" + new_phone

    data = await state.get_data()
    full_name = data.get("full_name", message.from_user.full_name)
    language = data.get("language", "uz")
    referred_by = data.get("referred_by")

    from data.config import ADMINS
    is_admin_user = str(message.from_user.id) in [str(a) for a in ADMINS]

    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        if user:
            user.full_name = full_name
            user.username = message.from_user.username
            user.phone = new_phone
            user.language = LanguageEnum(language) if isinstance(language, str) else language
            if is_admin_user:
                user.role = RoleEnum.admin
            if referred_by and not user.referred_by:
                user.referred_by = referred_by
        else:
            user = User(
                id=message.from_user.id,
                full_name=full_name,
                username=message.from_user.username,
                phone=message.contact.phone_number,
                language=LanguageEnum(language) if isinstance(language, str) else language,
                role=RoleEnum.admin if is_admin_user else RoleEnum.student,
                referred_by=referred_by,
                referral_code=f"ADMIN{message.from_user.id % 10000}" if is_admin_user else f"REF{message.from_user.id}",
            )
            session.add(user)
        await session.commit()

    # Taklif qilgan foydalanuvchiga bildirishnoma yuboramiz
    if referred_by:
        from main import bot
        try:
            await bot.send_message(
                referred_by,
                f"🎁 <b>Yangi referal qo'shildi!</b>\n\n"
                f"Do'stingiz <b>{full_name}</b> sizning taklif havolangiz orqali botga kirdi!\n\n"
                f"<i>Do'stingiz kurs uchun to'lov qilgandan so'ng, sizga navbatdagi oy uchun <b>+5% chegirma bonusi</b> beriladi.</i>"
            )
        except Exception:
            pass

    await state.clear()
    await message.answer(
        i18n.get("registration-done"),
        reply_markup=main_menu_keyboard(
            i18n,
            user_id=message.from_user.id,
            user_name=full_name,
            username=message.from_user.username,
            is_admin=is_admin_user,
        ),
    )


@router.message(Registration.entering_phone)
async def phone_invalid(message: Message, i18n: I18nContext):
    # Foydalanuvchi tugma o'rniga matn yozib yuborsa yoki boshqa narsa yuborsa
    await message.answer(
        "⚠️ <b>Telefon raqamni qo'lda yozish yoki forward qilish mumkin emas!</b>\n\n"
        "Iltimos, pastdagi <b>«📱 Raqamni yuborish»</b> tugmasini bosing.",
        reply_markup=phone_keyboard(i18n),
    )