import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from backend.services.ai_test_generator import generate_test_from_pdf_text

async def main():
    sample_text = """
    IELTS Placement Test - Section 1
    1. The government decided to ___ new measures to improve public transport.
    A) implement
    B) implementate
    C) illusion
    D) imagine

    2. She was not clear about the meeting time.
    A) true
    B) false

    3. If they had left earlier, they ___ missed the flight.
    A) wouldn't have
    B) won't have
    C) hadn't
    D) didn't
    """

    questions = await generate_test_from_pdf_text(sample_text, cert_type="IELTS", level="B2")
    print(f"Total questions generated: {len(questions)}")
    for q in questions:
        print(f"[{q['id']}] Q: {q['text'][:40]} | Options: {len(q.get('options') or [])} | Warning: {q.get('needs_review')}")

    assert len(questions) >= 3, "Expected at least 3 questions"
    print("ALL AI TEST GENERATOR TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(main())
