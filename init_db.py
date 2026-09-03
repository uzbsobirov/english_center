"""
Barcha jadvallarni yaratish, tozalash (reset) va boshlang'ich ma'lumotlarni kiritish skripti.
Foydalanish:
    python init_db.py          # Faqat yetishmayotgan jadvallarni va testlarni yaratadi
    python init_db.py --reset  # BAZANI TO'LIQ O'CHIRIB, BOSHIDAN YARATADI VA SEED QILADI
"""
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import asyncio
from sqlalchemy import select, text
from backend.database import engine, Base, async_session
from backend.models import (
    User, RoleEnum, LanguageEnum, LevelEnum, CourseTypeEnum,
    Course, Group, Test, TestSourceEnum, CenterSetting
)
from data.config import ADMINS
import backend.models  # Modellar ro'yxatdan o'tishi uchun


SAMPLE_TESTS = [
    # --- CEFR TESTLARI ---
    {
        "level": LevelEnum.A1,
        "certificate_type": "CEFR",
        "title": {"uz": "CEFR A1 — Beginner Test", "ru": "CEFR A1 — Тест для начинающих", "en": "CEFR A1 — Beginner Test"},
        "passing_score": 70.0,
        "time_limit_min": 15,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "cefr_a1_q1",
                "type": "mcq",
                "text": "What is the capital of the UK?",
                "options": ["Paris", "London", "Berlin", "Madrid"],
                "correct_answer": "London"
            },
            {
                "id": "cefr_a1_q2",
                "type": "mcq",
                "text": "She ___ a teacher.",
                "options": ["is", "am", "are", "be"],
                "correct_answer": "is"
            },
            {
                "id": "cefr_a1_q3",
                "type": "mcq",
                "text": "Choose the correct translation of 'kitob':",
                "options": ["book", "pen", "table", "chair"],
                "correct_answer": "book"
            }
        ]
    },
    {
        "level": LevelEnum.A2,
        "certificate_type": "CEFR",
        "title": {"uz": "CEFR A2 — Elementary Test", "ru": "CEFR A2 — Элементарный тест", "en": "CEFR A2 — Elementary Test"},
        "passing_score": 70.0,
        "time_limit_min": 15,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "cefr_a2_q1",
                "type": "mcq",
                "text": "Yesterday, we ___ to the cinema.",
                "options": ["go", "went", "gone", "going"],
                "correct_answer": "went"
            },
            {
                "id": "cefr_a2_q2",
                "type": "mcq",
                "text": "He is taller ___ his brother.",
                "options": ["then", "than", "as", "from"],
                "correct_answer": "than"
            },
            {
                "id": "cefr_a2_q3",
                "type": "mcq",
                "text": "How ___ sugar do you need?",
                "options": ["many", "much", "few", "any"],
                "correct_answer": "much"
            }
        ]
    },
    {
        "level": LevelEnum.B1,
        "certificate_type": "CEFR",
        "title": {"uz": "CEFR B1 — Intermediate Test", "ru": "CEFR B1 — Средний уровень", "en": "CEFR B1 — Intermediate Test"},
        "passing_score": 70.0,
        "time_limit_min": 20,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "cefr_b1_q1",
                "type": "mcq",
                "text": "If it rains tomorrow, we ___ at home.",
                "options": ["stay", "will stay", "stayed", "would stay"],
                "correct_answer": "will stay"
            },
            {
                "id": "cefr_b1_q2",
                "type": "mcq",
                "text": "I have lived here ___ 2018.",
                "options": ["for", "since", "during", "from"],
                "correct_answer": "since"
            },
            {
                "id": "cefr_b1_q3",
                "type": "mcq",
                "text": "The bridge ___ built in 1995.",
                "options": ["was", "is", "has been", "were"],
                "correct_answer": "was"
            }
        ]
    },
    {
        "level": LevelEnum.B2,
        "certificate_type": "CEFR",
        "title": {"uz": "CEFR B2 — Upper-Intermediate Test", "ru": "CEFR B2 — Выше среднего", "en": "CEFR B2 — Upper-Intermediate Test"},
        "passing_score": 70.0,
        "time_limit_min": 20,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "cefr_b2_q1",
                "type": "mcq",
                "text": "Hardly ___ entered the room when the phone rang.",
                "options": ["had I", "I had", "did I", "I did"],
                "correct_answer": "had I"
            },
            {
                "id": "cefr_b2_q2",
                "type": "mcq",
                "text": "He denied ___ the confidential documents.",
                "options": ["to take", "having taken", "take", "to have taken"],
                "correct_answer": "having taken"
            },
            {
                "id": "cefr_b2_q3",
                "type": "mcq",
                "text": "Choose the synonym for 'meticulous':",
                "options": ["careless", "diligent and thorough", "hurried", "lazy"],
                "correct_answer": "diligent and thorough"
            }
        ]
    },
    {
        "level": LevelEnum.C1,
        "certificate_type": "CEFR",
        "title": {"uz": "CEFR C1 — Advanced Test", "ru": "CEFR C1 — Продвинутый уровень", "en": "CEFR C1 — Advanced Test"},
        "passing_score": 70.0,
        "time_limit_min": 25,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "cefr_c1_q1",
                "type": "mcq",
                "text": "Had it not been for your assistance, I ___ succeeded.",
                "options": ["would never have", "would have never", "could have not", "will not have"],
                "correct_answer": "would never have"
            },
            {
                "id": "cefr_c1_q2",
                "type": "mcq",
                "text": "The government's proposal sparked a ___ debate among economists.",
                "options": ["fierce", "steep", "high", "deep"],
                "correct_answer": "fierce"
            },
            {
                "id": "cefr_c1_q3",
                "type": "mcq",
                "text": "The findings are ___ with the hypothesis proposed earlier.",
                "options": ["congruent", "dissimilar", "opposed", "indifferent"],
                "correct_answer": "congruent"
            }
        ]
    },
    {
        "level": LevelEnum.C2,
        "certificate_type": "CEFR",
        "title": {"uz": "CEFR C2 — Mastery Test", "ru": "CEFR C2 — Профессиональный уровень", "en": "CEFR C2 — Mastery Test"},
        "passing_score": 70.0,
        "time_limit_min": 25,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "cefr_c2_q1",
                "type": "mcq",
                "text": "The defendant's explanation was deemed entirely ___ by the jury.",
                "options": ["specious", "authentic", "candid", "veracious"],
                "correct_answer": "specious"
            },
            {
                "id": "cefr_c2_q2",
                "type": "mcq",
                "text": "Such egregious misconduct will not be ___ by the institution.",
                "options": ["countenanced", "repudiated", "abrogated", "disdained"],
                "correct_answer": "countenanced"
            },
            {
                "id": "cefr_c2_q3",
                "type": "mcq",
                "text": "His philosophical discourse was characterized by arcane ___ and convoluted reasoning.",
                "options": ["jargon", "lucidity", "brevity", "simplicity"],
                "correct_answer": "jargon"
            }
        ]
    },

    # --- IELTS TESTLARI ---
    {
        "level": LevelEnum.A1,
        "certificate_type": "IELTS",
        "title": {"uz": "IELTS Foundation (A1) Test", "ru": "IELTS Foundation (A1) Тест", "en": "IELTS Foundation (A1) Test"},
        "passing_score": 70.0,
        "time_limit_min": 15,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "ielts_a1_q1",
                "type": "mcq",
                "text": "IELTS Listening section has ___ parts.",
                "options": ["2", "3", "4", "5"],
                "correct_answer": "4"
            },
            {
                "id": "ielts_a1_q2",
                "type": "mcq",
                "text": "Choose the correct spelling:",
                "options": ["Accomodation", "Accommodation", "Acommodation", "Accomadation"],
                "correct_answer": "Accommodation"
            }
        ]
    },
    {
        "level": LevelEnum.A2,
        "certificate_type": "IELTS",
        "title": {"uz": "IELTS Pre-Intermediate (A2) Test", "ru": "IELTS Pre-Intermediate (A2) Тест", "en": "IELTS Pre-Intermediate (A2) Test"},
        "passing_score": 70.0,
        "time_limit_min": 15,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "ielts_a2_q1",
                "type": "mcq",
                "text": "In IELTS Task 1 General Training, candidates must write a:",
                "options": ["Letter", "Report", "Essay", "Summary"],
                "correct_answer": "Letter"
            },
            {
                "id": "ielts_a2_q2",
                "type": "mcq",
                "text": "According to the speaker, the flight was delayed ___ bad weather.",
                "options": ["because", "due to", "as", "since of"],
                "correct_answer": "due to"
            }
        ]
    },
    {
        "level": LevelEnum.B1,
        "certificate_type": "IELTS",
        "title": {"uz": "IELTS Band 5.0-5.5 (B1) Test", "ru": "IELTS Band 5.0-5.5 (B1) Тест", "en": "IELTS Band 5.0-5.5 (B1) Test"},
        "passing_score": 70.0,
        "time_limit_min": 20,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "ielts_b1_q1",
                "type": "mcq",
                "text": "Which linking word shows contrast?",
                "options": ["Furthermore", "Moreover", "However", "Therefore"],
                "correct_answer": "However"
            },
            {
                "id": "ielts_b1_q2",
                "type": "mcq",
                "text": "The proportion of renewable energy grew ___ between 2010 and 2020.",
                "options": ["dramatic", "dramatically", "dramatize", "drama"],
                "correct_answer": "dramatically"
            }
        ]
    },
    {
        "level": LevelEnum.B2,
        "certificate_type": "IELTS",
        "title": {"uz": "IELTS Band 6.0-6.5 (B2) Test", "ru": "IELTS Band 6.0-6.5 (B2) Тест", "en": "IELTS Band 6.0-6.5 (B2) Test"},
        "passing_score": 70.0,
        "time_limit_min": 20,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "ielts_b2_q1",
                "type": "mcq",
                "text": "In academic writing, 'a lot of people believe' can be best paraphrased as:",
                "options": ["It is widely believed that", "Many folks think", "Everybody knows", "People are saying"],
                "correct_answer": "It is widely believed that"
            },
            {
                "id": "ielts_b2_q2",
                "type": "mcq",
                "text": "The research ___ that regular exercise enhances cognitive function.",
                "options": ["indicates", "guesses", "wonders", "talks"],
                "correct_answer": "indicates"
            }
        ]
    },
    {
        "level": LevelEnum.C1,
        "certificate_type": "IELTS",
        "title": {"uz": "IELTS Band 7.0-8.0 (C1) Test", "ru": "IELTS Band 7.0-8.0 (C1) Тест", "en": "IELTS Band 7.0-8.0 (C1) Test"},
        "passing_score": 70.0,
        "time_limit_min": 25,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "ielts_c1_q1",
                "type": "mcq",
                "text": "Which word is closest in meaning to 'ubiquitous'?",
                "options": ["Omnipresent", "Scarce", "Obsolete", "Ambiguous"],
                "correct_answer": "Omnipresent"
            },
            {
                "id": "ielts_c1_q2",
                "type": "mcq",
                "text": "The author's tone in the passage can best be described as:",
                "options": ["Dispassionate", "Aggressive", "Facetious", "Indifferent"],
                "correct_answer": "Dispassionate"
            }
        ]
    },
    {
        "level": LevelEnum.C2,
        "certificate_type": "IELTS",
        "title": {"uz": "IELTS Band 8.5-9.0 (C2) Test", "ru": "IELTS Band 8.5-9.0 (C2) Тест", "en": "IELTS Band 8.5-9.0 (C2) Test"},
        "passing_score": 70.0,
        "time_limit_min": 25,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "ielts_c2_q1",
                "type": "mcq",
                "text": "His rhetoric was laden with subtle nuances that ___ any simplistic interpretation.",
                "options": ["defied", "endorsed", "perpetuated", "mimicked"],
                "correct_answer": "defied"
            },
            {
                "id": "ielts_c2_q2",
                "type": "mcq",
                "text": "The committee's verdict was ostensibly unanimous, notwithstanding several ___ dissenting memos.",
                "options": ["surreptitious", "blatant", "inconsequential", "ephemeral"],
                "correct_answer": "surreptitious"
            }
        ]
    }
]


async def seed_center_settings(session):
    res = await session.execute(select(CenterSetting))
    setting = res.scalars().first()
    if not setting:
        setting = CenterSetting(
            contact_phone="+998901234567",
            contact_username="english_center_admin",
            address={
                "uz": "Toshkent sh., Amir Temur ko'chasi, 12-uy",
                "ru": "г. Ташкент, ул. Амира Темура, д. 12",
                "en": "12 Amir Temur street, Tashkent"
            }
        )
        session.add(setting)
        print("  [+] Markaz sozlamalari (center_settings) kiritildi")


async def seed_admins(session):
    admin_ids = [int(a) for a in ADMINS if str(a).isdigit()]
    for aid in admin_ids:
        user = await session.get(User, aid)
        if not user:
            user = User(
                id=aid,
                full_name="Bosh Admin",
                username="admin",
                phone=None,
                role=RoleEnum.admin,
                language=LanguageEnum.uz,
                referral_code=f"ADMIN{aid % 10000}",
            )
            session.add(user)
            print(f"  [+] Bosh admin yaratildi (ID: {aid}, Roli: admin)")
        else:
            user.role = RoleEnum.admin
            if not user.referral_code:
                user.referral_code = f"ADMIN{aid % 10000}"
            print(f"  [+] Admin mavjud, roli yangilandi (ID: {aid})")


async def seed_courses_and_groups(session):
    # Asosiy admin ID sini topamiz
    admin_ids = [int(a) for a in ADMINS if str(a).isdigit()]
    teacher_id = admin_ids[0] if admin_ids else 1435473812

    # 1. Kurslar
    c1 = Course(
        title={"uz": "IELTS Intensive", "ru": "Интенсивный IELTS", "en": "IELTS Intensive"},
        type=CourseTypeEnum.IELTS,
        level=LevelEnum.B2,
        description={
            "uz": "IELTS 7.0+ olish uchun maxsus 3 oylik intensiv tayyorgarlik kursi.",
            "ru": "3-месячный интенсивный курс подготовки к IELTS 7.0+.",
            "en": "3-month intensive course for IELTS 7.0+."
        },
        duration_months=3,
        lessons_per_week=3,
        price=650000.0,
        price_per_lesson=54000.0,
        is_active=True
    )

    c2 = Course(
        title={"uz": "CEFR B1/B2 Comprehensive", "ru": "Комплексный CEFR B1/B2", "en": "CEFR B1/B2 Comprehensive"},
        type=CourseTypeEnum.CEFR,
        level=LevelEnum.B1,
        description={
            "uz": "Davlat attestatsiyasi va CEFR milliy sertifikati uchun to'liq kurs.",
            "ru": "Полный курс для национальной сертификации CEFR.",
            "en": "Comprehensive preparation for national CEFR certificate."
        },
        duration_months=4,
        lessons_per_week=3,
        price=500000.0,
        price_per_lesson=42000.0,
        is_active=True
    )

    c3 = Course(
        title={"uz": "General English (Elementary)", "ru": "Общий английский (Elementary)", "en": "General English (Elementary)"},
        type=CourseTypeEnum.General,
        level=LevelEnum.A2,
        description={
            "uz": "Noldan boshlab erkin muloqot va grammatikani mustahkamlash.",
            "ru": "Разговорный английский и базовая грамматика с нуля.",
            "en": "Spoken English and essential grammar from basics."
        },
        duration_months=3,
        lessons_per_week=3,
        price=450000.0,
        price_per_lesson=37500.0,
        is_active=True
    )

    session.add_all([c1, c2, c3])
    await session.flush()
    print("  [+] Kurslar yaratildi: IELTS Intensive, CEFR B1/B2, General English")

    # 2. Guruhlar
    g1 = Group(
        course_id=c1.id,
        teacher_id=teacher_id,
        name="IELTS-Morning-01",
        schedule=[{"day": 1, "time": "09:00"}, {"day": 3, "time": "09:00"}, {"day": 5, "time": "09:00"}],
        room="Auditoriya 101",
        max_students=12,
        group_chat_link="https://t.me/english_center_group1",
        is_active=True
    )

    g2 = Group(
        course_id=c2.id,
        teacher_id=teacher_id,
        name="CEFR-Evening-01",
        schedule=[{"day": 2, "time": "18:30"}, {"day": 4, "time": "18:30"}, {"day": 6, "time": "18:30"}],
        room="Auditoriya 102",
        max_students=10,
        group_chat_link="https://t.me/english_center_group2",
        is_active=True
    )

    g3 = Group(
        course_id=c3.id,
        teacher_id=teacher_id,
        name="General-Afternoon-01",
        schedule=[{"day": 1, "time": "15:00"}, {"day": 3, "time": "15:00"}, {"day": 5, "time": "15:00"}],
        room="Auditoriya 103",
        max_students=15,
        group_chat_link="https://t.me/english_center_group3",
        is_active=True
    )

    session.add_all([g1, g2, g3])
    print("  [+] Sinov guruhlari yaratildi: IELTS-Morning-01, CEFR-Evening-01, General-Afternoon-01")


async def seed_tests(session):
    for t_data in SAMPLE_TESTS:
        test = Test(
            certificate_type=t_data["certificate_type"],
            level=t_data["level"],
            title=t_data["title"],
            passing_score=t_data["passing_score"],
            time_limit_min=t_data["time_limit_min"],
            source=t_data["source"],
            questions=t_data["questions"],
            is_active=True,
        )
        session.add(test)
    print(f"  [+] Jami {len(SAMPLE_TESTS)} ta daraja testlari (A1-C2) kiritildi")


async def full_reset_and_init():
    print("=" * 60)
    print("⚠️  DATABASE TO'LIQ TOZALANMOQDA VA BOSHIDAN YARATILMOQDA...")
    print("=" * 60)

    async with engine.begin() as conn:
        print("[1/3] Jadvallarni o'chirish (DROP SCHEMA public CASCADE)...")
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        
        print("[2/3] Barcha yangi jadvallarni yaratish...")
        await conn.run_sync(Base.metadata.create_all)

    print("[3/3] Dastlabki ma'lumotlarni (seed data) kiritish...")
    async with async_session() as session:
        await seed_center_settings(session)
        await seed_admins(session)
        await seed_courses_and_groups(session)
        await seed_tests(session)
        await session.commit()

    print("=" * 60)
    print("✅ DATABASE TO'LIQ TOZALANDI VA TAYYOR HOLATGA KELTIRILDI!")
    print("=" * 60)


async def normal_init():
    print("[INFO] Mavjud jadvallarni tekshirish...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        await seed_center_settings(session)
        await seed_admins(session)
        res = await session.execute(select(Course))
        if not res.scalars().first():
            await seed_courses_and_groups(session)
        res_test = await session.execute(select(Test))
        if not res_test.scalars().first():
            await seed_tests(session)
        await session.commit()

    print("✅ Baza sozlandi!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--reset", "-r"):
        asyncio.run(full_reset_and_init())
    else:
        asyncio.run(normal_init())
