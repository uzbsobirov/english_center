"""
i18n manager: har bir foydalanuvchi uchun qaysi tilda javob berishni aniqlaydi.

MUHIM: aiogram_i18n BaseManager metodlariga argumentlarni parametr NOMIGA qarab
avtomatik uzatadi (aiogram middleware data dict'idan). Shuning uchun bu yerda
"event" yoki "data" degan umumiy parametr emas, aynan kerakli narsalarni
(event_from_user, state) alohida parametr sifatida yozamiz.
"""
from aiogram.fsm.context import FSMContext
from aiogram.types import User as TgUser
from aiogram_i18n.managers import BaseManager

from backend.database import async_session
from backend.models import User, LanguageEnum


class UserManager(BaseManager):

    async def get_locale(self, event_from_user: TgUser, state: FSMContext) -> str:
        # 1) Bazada mavjud foydalanuvchi tilini tekshiramiz (eng asosiy va birlamchi manba)
        if event_from_user is not None:
            async with async_session() as session:
                user = await session.get(User, event_from_user.id)
                if user is not None and user.language:
                    if user.username == "admin" or (event_from_user.username and user.username != event_from_user.username):
                        user.username = event_from_user.username
                        await session.commit()
                    # FSM state'dagi keshni ham yangi tilga sinxronlaymiz
                    if state is not None:
                        await state.update_data(language=user.language.value)
                    return user.language.value

        # 2) Agar foydalanuvchi hali bazada bo'lmasa (ro'yxatdan o'tish jarayonida), FSM'dan olamiz
        if state is not None:
            fsm_data = await state.get_data()
            lang = fsm_data.get("language")
            if lang:
                return lang

        # 3) Standart til
        return "uz"

    async def set_locale(self, locale: str, event_from_user: TgUser, state: FSMContext) -> None:
        """
        Foydalanuvchi tilni o'zgartirganda chaqiriladi (masalan '🌐 Til' tugmasi orqali).
        Ham FSM'ga, ham DB'ga yozib qo'yamiz.
        """
        if state is not None:
            await state.update_data(language=locale)

        if event_from_user is not None:
            async with async_session() as session:
                user = await session.get(User, event_from_user.id)
                if user is not None:
                    try:
                        user.language = LanguageEnum(locale)
                    except ValueError:
                        user.language = LanguageEnum.uz
                    await session.commit()