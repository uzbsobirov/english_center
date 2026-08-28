"""
👥 Referal bo'limi (TZ v2.6, 14 va 14.1-bo'lim).
- Shaxsiy referal havolasi
- Muvaffaqiyatli takliflar va to'plangan foizli chegirma (+5% har bir do'st uchun)
"""
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_i18n import I18nContext
from sqlalchemy import select, func

from backend.database import async_session
from backend.models import User, ReferralBonus

router = Router()

REFERRAL_BUTTON_TEXTS = {"👥 Referal", "👥 Реферал", "👥 Referral"}


from urllib.parse import quote
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions


@router.message(F.text.in_(REFERRAL_BUTTON_TEXTS))
async def show_referral(message: Message, i18n: I18nContext):
    if not message.from_user:
        return
    user_id = message.from_user.id

    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            return

        # Referal kod yaratamiz agar yo'q bo'lsa
        if not user.referral_code:
            user.referral_code = f"REF{user.id}"
            await session.commit()

        # Taklif qilingan do'stlar soni
        referred_count_res = await session.execute(
            select(func.count(User.id)).where(User.referred_by == user_id)
        )
        total_invited = referred_count_res.scalar() or 0

        # Jamlangan faol bonuslar foizi
        bonuses_res = await session.execute(
            select(ReferralBonus).where(
                ReferralBonus.user_id == user_id,
                ReferralBonus.is_used == False,
            )
        )
        bonuses = bonuses_res.scalars().all()
        total_discount = sum(float(b.bonus_percent) for b in bonuses)

    from main import bot
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user.referral_code}"

    text = (
        f"🎁 <b>Do'stlarni Taklif Qilish (Referal Dasturi)</b>\n\n"
        f"Do'stlaringizni markazimizga taklif qiling va har bir do'stingiz to'lov qilganda <b>+5% doimiy chegirma</b>ga ega bo'ling!\n\n"
        f"🔗 <b>Sizning shaxsiy referal havolangiz:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"📊 <b>Sizning statistikangiz:</b>\n"
        f"▫️ Taklif qilingan do'stlar: <b>{total_invited} ta</b>\n"
        f"▫️ To'plangan chegirma: <b>{total_discount:.1f}%</b>\n\n"
        f"<i>Chegirmalar har oy to'lovingizdan avtomatik chegirib boriladi.</i>"
    )

    share_text = (
        f"🚀 Alpha English Center bilan ingliz tilini 0 dan IELTS 7.5+ gacha professional darajada o'rganing!\n\n"
        f"✨ Bepul sinov darsi va interaktiv daraja testidan o'tish uchun quyidagi havolaga bosing:\n"
        f"👉 {ref_link}"
    )
    share_url = f"https://t.me/share/url?url={quote(ref_link)}&text={quote(share_text)}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Do'stlarga ulashish", url=share_url)]
    ])
    await message.answer(
        text,
        reply_markup=keyboard,
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )
