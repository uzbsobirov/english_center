import sys
import asyncio

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.database import async_session
from backend.models import Test, LevelEnum, TestSourceEnum

LEVEL_QUESTIONS = {
    LevelEnum.A2: [
        {"id": "q_1", "text": "I ___ go to the supermarket yesterday.", "options": ["A) doesn't", "B) didn't", "C) don't", "D) wasn't"], "correct": "B) didn't"},
        {"id": "q_2", "text": "She is taller ___ her sister.", "options": ["A) that", "B) than", "C) then", "D) as"], "correct": "B) than"},
        {"id": "q_3", "text": "Have you ever ___ to London?", "options": ["A) be", "B) been", "C) was", "D) gone"], "correct": "B) been"},
    ],
    LevelEnum.B1: [
        {"id": "q_1", "text": "If it rains tomorrow, we ___ the picnic.", "options": ["A) cancel", "B) will cancel", "C) would cancel", "D) cancelled"], "correct": "B) will cancel"},
        {"id": "q_2", "text": "The bridge ___ built in 1995.", "options": ["A) was", "B) is", "C) has", "D) were"], "correct": "A) was"},
        {"id": "q_3", "text": "I look forward to ___ you soon.", "options": ["A) meet", "B) meeting", "C) met", "D) to meet"], "correct": "B) meeting"},
    ],
    LevelEnum.B2: [
        {"id": "q_1", "text": "Hardly ___ entered the room when the phone rang.", "options": ["A) had he", "B) he had", "C) did he", "D) he did"], "correct": "A) had he"},
        {"id": "q_2", "text": "You shouldn't have ___ him that secret.", "options": ["A) tell", "B) told", "C) telling", "D) tells"], "correct": "B) told"},
        {"id": "q_3", "text": "He managed to pass the exam in spite of ___ sick.", "options": ["A) being", "B) be", "C) to be", "D) been"], "correct": "A) being"},
    ],
    LevelEnum.C1: [
        {"id": "q_1", "text": "Under no circumstances ___ leave the building.", "options": ["A) you should", "B) should you", "C) you must", "D) will you"], "correct": "B) should you"},
        {"id": "q_2", "text": "The company's profits have soared, ___ widespread praise.", "options": ["A) garnering", "B) garnishing", "C) gleaming", "D) glancing"], "correct": "A) garnering"},
        {"id": "q_3", "text": "Had I known about the delay, I ___ another flight.", "options": ["A) would book", "B) would have booked", "C) had booked", "D) will book"], "correct": "B) would have booked"},
    ],
    LevelEnum.C2: [
        {"id": "q_1", "text": "His argument was entirely devoid ___ logic.", "options": ["A) in", "B) of", "C) from", "D) with"], "correct": "B) of"},
        {"id": "q_2", "text": "The novel's protagonist is an utterly ___ character, inspiring both pity and revulsion.", "options": ["A) ambivalent", "B) ambiguous", "C) amicable", "D) ubiquitous"], "correct": "A) ambivalent"},
        {"id": "q_3", "text": "So engrossing ___ the lecture that nobody noticed the time.", "options": ["A) was", "B) did", "C) had", "D) is"], "correct": "A) was"},
    ],
}

async def seed_tests():
    async with async_session() as session:
        from sqlalchemy import select
        for level, qs in LEVEL_QUESTIONS.items():
            existing = (await session.execute(
                select(Test).where(Test.level == level, Test.is_active == True)
            )).scalars().first()

            if not existing:
                t = Test(
                    teacher_id=1435473812,
                    certificate_type="placement",
                    level=level,
                    title={"uz": f"{level.value} Placement Test", "ru": f"{level.value} Тест", "en": f"{level.value} Placement Test"},
                    passing_score=2,
                    time_limit_min=15,
                    source=TestSourceEnum.manual,
                    questions=qs,
                    is_active=True
                )
                session.add(t)
                print(f"✅ Created placement test for level: {level.value}")
        await session.commit()

if __name__ == "__main__":
    asyncio.run(seed_tests())
