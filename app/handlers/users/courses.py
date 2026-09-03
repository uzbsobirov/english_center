"""
📚 Kurslar bo'limi (TZ v2.6, 16.3-bo'lim).
- Faol kurslar inline tugmalar ko'rinishida chiqadi
- Tanlanganda guruhlar, o'qituvchi username linki, dars kunlari/vaqti va bo'sh joylar soni ko'rsatiladi
- Har bir guruh ostida «📝 Free darsga yozilish» tugmasi
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_i18n import I18nContext
from sqlalchemy import select, func

from backend.database import async_session
from backend.models import Course, Group, User, Enrollment, FreeTrialRequest, FreeTrialStatusEnum

router = Router()

COURSE_BUTTON_TEXTS = {"📚 Kurslar", "📚 Курсы", "📚 Courses"}


@router.message(F.text.in_(COURSE_BUTTON_TEXTS))
async def show_courses(message: Message, i18n: I18nContext):
    async with async_session() as session:
        result = await session.execute(
            select(Course).where(Course.is_active == True)
        )
        courses = result.scalars().all()

    if not courses:
        await message.answer("Hozirda faol kurslar mavjud emas.")
        return

    lang = i18n.locale
    buttons = []
    for c in courses:
        title = c.title.get(lang, c.title.get("uz", "Kurs")) if isinstance(c.title, dict) else str(c.title)
        buttons.append([
            InlineKeyboardButton(
                text=f"{title} ({c.type.value if hasattr(c.type, 'value') else c.type} {c.level.value})",
                callback_data=f"course_detail:{c.id}",
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("📚 Bizning mavjud kurslarimiz:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("course_detail:"))
async def course_detail_callback(callback: CallbackQuery, i18n: I18nContext):
    course_id = int(callback.data.split(":")[1])
    lang = i18n.locale

    async with async_session() as session:
        course = await session.get(Course, course_id)
        if not course:
            await callback.answer("Kurs topilmadi.", show_alert=True)
            return

        groups_res = await session.execute(
            select(Group).where(Group.course_id == course_id, Group.is_active == True)
        )
        groups = groups_res.scalars().all()

    title = course.title.get(lang, course.title.get("uz", "")) if isinstance(course.title, dict) else str(course.title)
    desc = course.description.get(lang, course.description.get("uz", "")) if isinstance(course.description, dict) else ""

    text = [
        f"📚 <b>{title}</b>",
        f"🎯 Daraja: <b>{course.level.value}</b>",
        f"⏱ Davomiyligi: <b>{course.duration_months} oy</b> ({course.lessons_per_week} marta/hafta)",
        f"💰 Narxi: <b>{float(course.price):,.0f} so'm/oy</b>\n",
        f"{desc}\n",
        "👥 <b>Mavjud guruhlar:</b>"
    ]

    buttons = []
    if not groups:
        text.append("<i>Hozircha bu kurs bo'yicha ochiq guruhlar yo'q.</i>")
    else:
        for g in groups:
            # Teacher username va band joylar sonini aniqlaymiz
            async with async_session() as session:
                teacher = await session.get(User, g.teacher_id)
                enrolled_count_res = await session.execute(
                    select(func.count(Enrollment.id)).where(
                        Enrollment.group_id == g.id,
                        Enrollment.is_active == True,
                    )
                )
                enrolled_count = enrolled_count_res.scalar() or 0

            teacher_link = f"@{teacher.username}" if (teacher and teacher.username) else (teacher.full_name if teacher else "Noma'lum")
            free_slots = max(g.max_students - enrolled_count, 0)

            # Jadval formatlash
            sched_str = ", ".join([f"{item.get('day')}-kun {item.get('time')}" for item in g.schedule]) if g.schedule else "Kelishiladi"

            text.append(
                f"\n▫️ <b>{g.name}</b>\n"
                f"   👨‍🏫 O'qituvchi: {teacher_link}\n"
                f"   🗓 Jadval: {sched_str}\n"
                f"   🪑 Bo'sh joylar: <b>{free_slots} / {g.max_students}</b>"
            )

            buttons.append([
                InlineKeyboardButton(
                    text=f"📝 Free darsga yozilish ({g.name})",
                    callback_data=f"book_trial_group:{g.id}",
                ),
                InlineKeyboardButton(
                    text=f"💳 To'lov qilish",
                    callback_data=f"pay_group:{g.id}",
                )
            ])

    buttons.append([InlineKeyboardButton(text="◀️ Ortga", callback_data="courses_back")])
    await callback.message.edit_text("\n".join(text), reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data == "courses_back")
async def courses_back_callback(callback: CallbackQuery, i18n: I18nContext):
    async with async_session() as session:
        result = await session.execute(select(Course).where(Course.is_active == True))
        courses = result.scalars().all()

    lang = i18n.locale
    buttons = [
        [InlineKeyboardButton(
            text=f"{c.title.get(lang, c.title.get('uz', 'Kurs'))} ({c.type.value if hasattr(c.type, 'value') else c.type} {c.level.value})",
            callback_data=f"course_detail:{c.id}",
        )]
        for c in courses
    ]
    await callback.message.edit_text("📚 Bizning mavjud kurslarimiz:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


import urllib.parse
from data.config import get_webapp_url
from aiogram.types import WebAppInfo
from backend.models import TestResult, Test


@router.callback_query(F.data.startswith("book_trial_group:"))
async def book_trial_group_callback(callback: CallbackQuery, i18n: I18nContext):
    group_id = int(callback.data.split(":")[1])
    student_id = callback.from_user.id

    async with async_session() as session:
        group = await session.get(Group, group_id)
        if not group:
            await callback.answer("Guruh topilmadi.", show_alert=True)
            return

        course = await session.get(Course, group.course_id)
        if not course:
            await callback.answer("Kurs topilmadi.", show_alert=True)
            return

        # O'quvchi shu daraja testidan o'tganligini tekshiramiz
        test_res = await session.execute(
            select(TestResult)
            .join(Test, TestResult.test_id == Test.id)
            .where(
                TestResult.student_id == student_id,
                TestResult.passed == True,
                Test.level == course.level,
            )
            .order_by(TestResult.created_at.desc())
        )
        passed_test = test_res.scalars().first()

        if not passed_test:
            # Test topshirilmagan bo'lsa - avval testga yo'naltiramiz
            base_url = get_webapp_url()
            sep = "&" if "?" in base_url else "?"
            cert_t = course.type.value if hasattr(course.type, 'value') else course.type
            user_name = callback.from_user.full_name or ""
            username = callback.from_user.username or ""
            locale_code = getattr(i18n, "locale", "uz") or "uz"
            test_url = (
                f"{base_url}{sep}level={course.level.value}&type={cert_t}&lang={locale_code}"
                f"&user_id={student_id}&name={urllib.parse.quote(user_name)}&username={urllib.parse.quote(username)}"
                f"&is_trial=true"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"🎯 {course.level.value} Testini Boshlash", web_app=WebAppInfo(url=test_url))]
            ])
            await callback.message.answer(
                f"🎯 <b>{group.name}</b> guruhiga bepul sinov darsiga yozilish uchun avval qisqa daraja testingizni topshirishingiz kerak.\n\n"
                f"📚 Daraja: <b>{course.level.value}</b>\n"
                f"📊 O'tish bali: <b>70%</b>\n\n"
                f"Testdan muvaffaqiyatli o'tganingizdan so'ng, bepul dars so'rovingiz avtomatik o'qituvchiga yuboriladi.",
                reply_markup=keyboard,
            )
            await callback.answer()
            return

        # Test topshirilgan bo'lsa - so'rov yaratamiz
        trial = FreeTrialRequest(
            student_id=student_id,
            group_id=group_id,
            test_result_id=passed_test.id,
            status=FreeTrialStatusEnum.pending,
        )
        session.add(trial)
        await session.commit()
        trial_id = trial.id

    # O'qituvchiga xabar
    from main import bot
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"trial_accept:{trial_id}")
    ]])
    try:
        await bot.send_message(
            group.teacher_id,
            f"🆕 Yangi free-dars so'rovi!\n\n"
            f"O'quvchi: {callback.from_user.full_name}\n"
            f"Guruh: {group.name}\n"
            f"Daraja testi bali: {passed_test.percent:.1f}%\n\n"
            f"Free darsni qabul qilish uchun tugmani bosing:",
            reply_markup=keyboard,
        )
    except Exception:
        pass

    await callback.message.answer(
        f"📩 <b>{group.name}</b> guruhi uchun bepul sinov darsi so'rovingiz o'qituvchiga yuborildi!\n\n"
        f"👨‍🏫 O'qituvchi dars vaqti va manzilini tasdiqlashi bilan bot orqali sizga xabar beramiz."
    )
    await callback.answer()
