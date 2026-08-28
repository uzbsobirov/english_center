"""
Barcha jadvallarni yaratish va boshlang'ich sozlamalarni kiritish skripti.
"""
import asyncio
from sqlalchemy import select
from backend.database import engine, Base, async_session
from backend.models import Test, LevelEnum, TestSourceEnum
import backend.models  # Modellar ro'yxatdan o'tishi uchun

SAMPLE_TESTS = [
    {
        "level": LevelEnum.A1,
        "certificate_type": "CEFR",
        "title": {"uz": "A1 — Beginner Test", "ru": "A1 — Тест для начинающих", "en": "A1 — Beginner Test"},
        "passing_score": 70.0,
        "time_limit_min": 15,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "a1_q1",
                "type": "mcq",
                "text": "What is the capital of the UK?",
                "options": ["Paris", "London", "Berlin", "Madrid"],
                "correct_answer": "London"
            },
            {
                "id": "a1_q2",
                "type": "mcq",
                "text": "She ___ a teacher.",
                "options": ["is", "am", "are", "be"],
                "correct_answer": "is"
            },
            {
                "id": "a1_q3",
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
        "title": {"uz": "A2 — Elementary Test", "ru": "A2 — Элементарный тест", "en": "A2 — Elementary Test"},
        "passing_score": 70.0,
        "time_limit_min": 15,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "a2_q1",
                "type": "mcq",
                "text": "Yesterday, we ___ to the cinema.",
                "options": ["go", "went", "gone", "going"],
                "correct_answer": "went"
            },
            {
                "id": "a2_q2",
                "type": "mcq",
                "text": "He is taller ___ his brother.",
                "options": ["then", "than", "as", "from"],
                "correct_answer": "than"
            },
            {
                "id": "a2_q3",
                "type": "mcq",
                "text": "How ___ sugar do you need?",
                "options": ["many", "much", "few", "any"],
                "correct_answer": "much"
            }
        ]
    },
    {
        "level": LevelEnum.B1,
        "certificate_type": "IELTS",
        "title": {"uz": "B1 — Intermediate Test", "ru": "B1 — Средний уровень", "en": "B1 — Intermediate Test"},
        "passing_score": 70.0,
        "time_limit_min": 20,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "b1_q1",
                "type": "mcq",
                "text": "If it rains tomorrow, we ___ at home.",
                "options": ["stay", "will stay", "stayed", "would stay"],
                "correct_answer": "will stay"
            },
            {
                "id": "b1_q2",
                "type": "mcq",
                "text": "I have lived here ___ 2018.",
                "options": ["for", "since", "during", "from"],
                "correct_answer": "since"
            },
            {
                "id": "b1_q3",
                "type": "mcq",
                "text": "The bridge ___ built in 1995.",
                "options": ["was", "is", "has been", "were"],
                "correct_answer": "was"
            }
        ]
    },
    {
        "level": LevelEnum.B2,
        "certificate_type": "IELTS",
        "title": {"uz": "B2 — Upper-Intermediate Test", "ru": "B2 — Выше среднего", "en": "B2 — Upper-Intermediate Test"},
        "passing_score": 70.0,
        "time_limit_min": 20,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "b2_q1",
                "type": "mcq",
                "text": "Hardly had I arrived at the station ___ the train departed.",
                "options": ["than", "when", "then", "that"],
                "correct_answer": "when"
            },
            {
                "id": "b2_q2",
                "type": "mcq",
                "text": "She regretted ___ so much money on things she didn't need.",
                "options": ["to spend", "spending", "spent", "spend"],
                "correct_answer": "spending"
            },
            {
                "id": "b2_q3",
                "type": "mcq",
                "text": "Had I known about the meeting, I ___ attended.",
                "options": ["would have", "will have", "would", "had"],
                "correct_answer": "would have"
            }
        ]
    },
    {
        "level": LevelEnum.C1,
        "certificate_type": "IELTS",
        "title": {"uz": "C1 — Advanced Test", "ru": "C1 — Продвинутый уровень", "en": "C1 — Advanced Test"},
        "passing_score": 70.0,
        "time_limit_min": 25,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "c1_q1",
                "type": "mcq",
                "text": "The economic indicators were ___ ambiguous, perplexing even veteran analysts.",
                "options": ["decidedly", "scarcely", "partially", "reluctantly"],
                "correct_answer": "decidedly"
            },
            {
                "id": "c1_q2",
                "type": "mcq",
                "text": "Seldom ___ such remarkable dedication in a novice apprentice.",
                "options": ["we have witnessed", "have we witnessed", "we witnessed", "witnessed we"],
                "correct_answer": "have we witnessed"
            }
        ]
    },
    {
        "level": LevelEnum.C2,
        "certificate_type": "IELTS",
        "title": {"uz": "C2 — Proficiency Test", "ru": "C2 — Профессиональный уровень", "en": "C2 — Proficiency Test"},
        "passing_score": 70.0,
        "time_limit_min": 25,
        "source": TestSourceEnum.manual,
        "questions": [
            {
                "id": "c2_q1",
                "type": "mcq",
                "text": "His rhetoric was laden with subtle nuances that ___ any simplistic interpretation.",
                "options": ["defied", "endorsed", "perpetuated", "mimicked"],
                "correct_answer": "defied"
            },
            {
                "id": "c2_q2",
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
                select(Test).where(Test.level == t_data["level"], Test.is_active == True)
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
                print(f"[SEED] Test yaratildi: {t_data['level'].value}")
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


