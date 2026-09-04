import asyncio
import sys
import os
import copy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from backend.database import async_session
from backend.models import Test

async def fix_all_test_questions():
    async with async_session() as session:
        tests = (await session.execute(select(Test))).scalars().all()
        for t in tests:
            raw_questions = copy.deepcopy(t.questions or [])
            for q in raw_questions:
                corr = q.get("correct_answer") or q.get("correct")
                if corr:
                    q["correct_answer"] = corr
                    q["correct"] = corr
            t.questions = raw_questions
            flag_modified(t, "questions")

            # passing_score ni to'g'rilash (agar 2.0 bo'lib qolgan bo'lsa 70.0 ga)
            if float(t.passing_score) < 10.0:
                t.passing_score = 70.0
                print(f"  [Fix] Test #{t.id} ({t.level}): passing_score 70.0% ga o'zgartirildi")

            print(f"  [Fix] Test #{t.id} ({t.level}): {len(raw_questions)} ta savolda to'g'ri javoblar sinxronlandi")

        await session.commit()
        print("✅ Barcha test savollari va to'g'ri javoblari bazada to'liq tuzatildi!")

if __name__ == "__main__":
    asyncio.run(fix_all_test_questions())
