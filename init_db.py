"""
Barcha jadvallarni yaratish va boshlang'ich sozlamalarni kiritish skripti.
"""
import asyncio
from sqlalchemy import select
from backend.database import engine, Base, async_session
from backend.models import Test, LevelEnum, TestSourceEnum
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
                "text": "Hardly had I arrived at the station ___ the train departed.",
                "options": ["than", "when", "then", "that"],
                "correct_answer": "when"
            },
            {
                "id": "cefr_b2_q2",
                "type": "mcq",
                "text": "She regretted ___ so much money on things she didn't need.",
                "options": ["to spend", "spending", "spent", "spend"],
                "correct_answer": "spending"
            },
            {
                "id": "cefr_b2_q3",
                "type": "mcq",
                "text": "Had I known about the meeting, I ___ attended.",
                "options": ["would have", "will have", "would", "had"],
                "correct_answer": "would have"
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
                "text": "The economic indicators were ___ ambiguous, perplexing even veteran analysts.",
                "options": ["decidedly", "scarcely", "partially", "reluctantly"],
                "correct_answer": "decidedly"
            },
            {
                "id": "cefr_c1_q2",
                "type": "mcq",
                "text": "Seldom ___ such remarkable dedication in a novice apprentice.",
                "options": ["we have witnessed", "have we witnessed", "we witnessed", "witnessed we"],
                "correct_answer": "have we witnessed"
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
                "text": "Choose the correct spelling:",
                "options": ["Accomodation", "Accommodation", "Acomodation", "Acommodation"],
                "correct_answer": "Accommodation"
            },
            {
                "id": "ielts_a1_q2",
                "type": "mcq",
                "text": "There ___ many books on the shelf.",
                "options": ["is", "are", "be", "was"],
                "correct_answer": "are"
            }
        ]
    },
    {
        "level": LevelEnum.A2,
        "certificate_type": "IELTS",
        "title": {"uz": "IELTS Pre-Band 4.5 (A2) Test", "ru": "IELTS Pre-Band 4.5 (A2) Тест", "en": "IELTS Pre-Band 4.5 (A2) Test"},
        "passing_score": 70.0,
        "time_limit_min": 15,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "ielts_a2_q1",
                "type": "mcq",
                "text": "The graph shows a significant ___ in sales last year.",
                "options": ["increase", "increasing", "increased", "increasement"],
                "correct_answer": "increase"
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


async def seed_tests():
    async with async_session() as session:
        for t_data in SAMPLE_TESTS:
            res = await session.execute(
                select(Test).where(
                    Test.certificate_type == t_data["certificate_type"],
                    Test.level == t_data["level"],
                    Test.is_active == True,
                )
            )
            existing = res.scalars().first()
            if not existing:
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
                print(f"[SEED] Test yaratildi: {t_data['certificate_type']} - {t_data['level'].value}")
        await session.commit()


async def init_database():
    print("[INFO] Database jadvallarini yaratish boshlandi...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[SUCCESS] Barcha jadvallar muvaffaqiyatli yaratildi!")
    await seed_tests()
    print("[SUCCESS] Boshlang'ich testlar tayyor!")


if __name__ == "__main__":
    asyncio.run(init_database())
