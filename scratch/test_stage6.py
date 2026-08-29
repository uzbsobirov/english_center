import asyncio
from sqlalchemy import select, delete

from backend.database import async_session
from backend.models import User, RoleEnum, UserBadge, TestResult
from backend.services.gamification import (
    award_badge_if_eligible, check_test_badges, get_user_badges_summary, BADGE_INFO
)
from backend.services.certificate_generator import generate_certificate_pdf

async def run_stage6_tests():
    print("--- [TEST] Running Stage 6 (Gamification & Certificates) Test Suite ---")

    student_id = 999555666

    async with async_session() as session:
        # Clean
        await session.execute(delete(UserBadge).where(UserBadge.user_id == student_id))
        await session.execute(delete(TestResult).where(TestResult.student_id == student_id))
        await session.execute(delete(User).where(User.id == student_id))
        await session.commit()

        student = User(id=student_id, full_name="Sherzod Karimov", role=RoleEnum.student)
        session.add(student)
        await session.commit()

    # 1. Test Award Badges
    for badge_key in ["starter", "top_student", "regular", "ambassador", "level_up", "diligent", "graduate"]:
        awarded = await award_badge_if_eligible(student_id, badge_key)
        assert awarded == True, f"Failed to award {badge_key}"

    # Try duplicate award (should return False)
    dup = await award_badge_if_eligible(student_id, "starter")
    assert dup == False, "Duplicate badge should not be awarded"

    badges = await get_user_badges_summary(student_id)
    assert len(badges) == 7, f"Expected 7 badges, got {len(badges)}"
    print(f"[OK] Gamification: All 7 badges awarded successfully -> {', '.join(badges)}")

    # 2. Test Certificate Generator (ReportLab PDF)
    pdf_bytes = generate_certificate_pdf(
        student_name="Sherzod Karimov",
        course_type="IELTS Intensive",
        level="C1",
        certificate_id="CERT-2026-0001",
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000, f"Expected PDF > 1000 bytes, got {len(pdf_bytes)}"
    assert pdf_bytes.startswith(b"%PDF"), "Generated file is not a valid PDF"
    print(f"[OK] Certificate Generator: PDF created successfully (Size: {len(pdf_bytes)} bytes)")

    # Cleanup
    async with async_session() as session:
        await session.execute(delete(UserBadge).where(UserBadge.user_id == student_id))
        await session.execute(delete(TestResult).where(TestResult.student_id == student_id))
        await session.execute(delete(User).where(User.id == student_id))
        await session.commit()
        print("[OK] Test database cleaned up.")

    print("--- [ALL STAGE 6 TESTS PASSED] ---")

if __name__ == "__main__":
    asyncio.run(run_stage6_tests())
