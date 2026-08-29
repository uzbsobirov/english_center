import asyncio
from datetime import datetime, date, timedelta
from sqlalchemy import select, delete

from backend.database import async_session
from backend.models import (
    User, RoleEnum, Group, Course, Enrollment, LevelEnum,
    Attendance, AttendanceStatusEnum, Homework, UserBadge,
    SupportChat, SupportChatStatusEnum, SupportChatClosedReasonEnum,
)
from backend.services.gamification import award_badge_if_eligible
from backend.services.scheduler import check_support_chat_timeouts, check_homework_reminders

class MockBot:
    def __init__(self):
        self.sent_messages = []

    async def send_message(self, chat_id, text, **kwargs):
        self.sent_messages.append({"chat_id": chat_id, "text": text})

    async def send_document(self, chat_id, file_id, caption=None, **kwargs):
        self.sent_messages.append({"chat_id": chat_id, "file_id": file_id, "caption": caption})

async def run_stage4_tests():
    print("--- [TEST] Running Stage 4 (Attendance, Homework & Schedulers) Test Suite ---")
    mock_bot = MockBot()

    async with async_session() as session:
        # 1. Setup sample users: Teacher, Student
        teacher_id = 999333444
        student_id = 999222333

        # Clean
        await session.execute(delete(UserBadge).where(UserBadge.user_id == student_id))
        await session.execute(delete(Homework).where(Homework.teacher_id == teacher_id))
        await session.execute(delete(Attendance).where(Attendance.student_id == student_id))
        await session.execute(delete(Enrollment).where(Enrollment.student_id == student_id))
        await session.execute(delete(SupportChat).where(SupportChat.student_id == student_id))
        await session.execute(delete(User).where(User.id.in_([teacher_id, student_id])))
        await session.commit()

        teacher = User(id=teacher_id, full_name="Teacher Jasur", role=RoleEnum.teacher)
        student = User(id=student_id, full_name="Student Bobur", role=RoleEnum.student)
        session.add_all([teacher, student])

        # Get or create Course & Group
        course_res = await session.execute(select(Course).limit(1))
        course = course_res.scalars().first()
        if not course:
            course = Course(title={"uz": "IELTS Foundation"}, level=LevelEnum.B2, price=700000.0)
            session.add(course)
            await session.flush()

        group_res = await session.execute(select(Group).where(Group.course_id == course.id).limit(1))
        group = group_res.scalars().first()
        if not group:
            group = Group(name="IELTS-Evening", course_id=course.id, teacher_id=teacher_id)
            session.add(group)
            await session.flush()

        enrollment = Enrollment(student_id=student_id, group_id=group.id)
        session.add(enrollment)
        await session.commit()
        print(f"[OK] Setup Teacher ({teacher_id}), Student ({student_id}), Group ({group.name}).")

        # 2. Test Attendance & Gamification (10 Attendances -> Regular Badge)
        for i in range(10):
            att = Attendance(
                group_id=group.id,
                student_id=student_id,
                lesson_date=date.today() - timedelta(days=i),
                status=AttendanceStatusEnum.present,
                marked_by=teacher_id,
            )
            session.add(att)
        await session.commit()

        # Check regular badge award
        awarded = await award_badge_if_eligible(student_id, "regular")
        assert awarded == True, "Expected Regular badge to be awarded"
        print("[OK] 10 Attendances recorded -> Regular badge awarded successfully.")

        # 3. Test Homework Creation & Student Retrieval
        hw = Homework(
            group_id=group.id,
            teacher_id=teacher_id,
            title="Unit 5 — IELTS Reading Practice",
            description="Complete passage 1 and 2",
            file_id="BQACAgIAAxkBAAI...",
            due_at=datetime.utcnow() + timedelta(days=2),
            lesson_date=date.today(),
        )
        session.add(hw)
        await session.commit()

        # Retrieve as student
        hw_query = await session.execute(
            select(Homework).where(Homework.group_id == group.id).order_by(Homework.created_at.desc())
        )
        saved_hw = hw_query.scalars().first()
        assert saved_hw is not None
        assert saved_hw.title == "Unit 5 — IELTS Reading Practice"
        print(f"[OK] Homework created and retrieved: {saved_hw.title} (File: {saved_hw.file_id})")

        # 4. Test Support Chat Timeout Auto-Close (TZ 16.2)
        expired_chat = SupportChat(
            student_id=student_id,
            admin_id=teacher_id,
            status=SupportChatStatusEnum.open,
            last_message_at=datetime.utcnow() - timedelta(minutes=20),
        )
        session.add(expired_chat)
        await session.commit()
        chat_id = expired_chat.id

    # Check timeouts outside outer session
    await check_support_chat_timeouts(mock_bot)

    async with async_session() as session:
        chat_check = await session.get(SupportChat, chat_id)
        assert chat_check.status == SupportChatStatusEnum.closed
        assert chat_check.closed_reason == SupportChatClosedReasonEnum.timeout
        print(f"[OK] Support chat timeout verified: Chat ID={chat_id} automatically closed after 15+ min.")

        # 5. Test Homework Reminder Scheduler
        await check_homework_reminders(mock_bot)
        print("[OK] Homework reminders background check executed without errors.")

        # Cleanup
        await session.execute(delete(UserBadge).where(UserBadge.user_id == student_id))
        await session.execute(delete(Homework).where(Homework.teacher_id == teacher_id))
        await session.execute(delete(Attendance).where(Attendance.student_id == student_id))
        await session.execute(delete(Enrollment).where(Enrollment.student_id == student_id))
        await session.execute(delete(SupportChat).where(SupportChat.student_id == student_id))
        await session.execute(delete(User).where(User.id.in_([teacher_id, student_id])))
        await session.commit()
        print("[OK] Cleaned up test database.")

    print("--- [ALL STAGE 4 TESTS PASSED] ---")

if __name__ == "__main__":
    asyncio.run(run_stage4_tests())
