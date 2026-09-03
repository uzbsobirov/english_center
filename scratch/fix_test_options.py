import asyncio
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import copy
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from backend.database import async_session
from backend.models import Test

async def fix_test_options():
    async with async_session() as session:
        tests = (await session.execute(select(Test))).scalars().all()
        for t in tests:
            raw_questions = copy.deepcopy(t.questions or [])
            for idx, q in enumerate(raw_questions):
                opts = list(q.get("options", []))
                if len(opts) == 3:
                    if "am" in str(opts[0]) or "is" in str(opts[1]):
                        opts.append("D) were")
                    elif "small" in str(opts[0]):
                        opts.append("D) wide")
                    else:
                        opts.append("D) None of the above")
                q["options"] = opts
            
            t.questions = raw_questions
            flag_modified(t, "questions")
        
        await session.commit()
        print("✅ Fixed all test questions and committed with flag_modified!")

if __name__ == "__main__":
    asyncio.run(fix_test_options())
