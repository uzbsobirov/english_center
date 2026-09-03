import asyncio
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from backend.database import async_session
from backend.models import Test

async def inspect_tests():
    async with async_session() as session:
        tests = (await session.execute(select(Test))).scalars().all()
        print(f"Total tests: {len(tests)}")
        for t in tests:
            print(f"\n--- Test ID {t.id} | Level: {t.level} | Title: {t.title} ---")
            for idx, q in enumerate(t.questions or []):
                opts = q.get("options", [])
                ans = q.get("correct_answer") or q.get("answer")
                print(f"  Q{idx+1}: {q.get('text', q.get('question'))[:40]}... Options ({len(opts)}): {opts} | Ans: {ans}")

if __name__ == "__main__":
    asyncio.run(inspect_tests())
