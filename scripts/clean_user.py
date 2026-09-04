"""
Foydalanuvchini va unga bog'langan barcha ma'lumotlarni tozalash skripti.
Foydalanish:
    python clean_user.py <telegram_id>
    yoki barcha test o'quvchilarni tozalash (admin saqlanadi):
    python clean_user.py --all-students
"""
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from sqlalchemy import text
from backend.database import async_session
from data.config import ADMINS


async def delete_single_user(user_id: int):
    async with async_session() as session:
        print(f"🗑 Foydalanuvchi ({user_id}) ma'lumotlari o'chirilmoqda...")
        queries = [
            text("DELETE FROM homework_submissions WHERE student_id = :uid"),
            text("DELETE FROM attendance WHERE student_id = :uid"),
            text("DELETE FROM test_results WHERE student_id = :uid"),
            text("DELETE FROM free_trial_requests WHERE student_id = :uid"),
            text("DELETE FROM enrollments WHERE student_id = :uid"),
            text("DELETE FROM support_chats WHERE student_id = :uid"),
            text("DELETE FROM payments WHERE student_id = :uid"),
            text("DELETE FROM referral_bonuses WHERE user_id = :uid"),
            text("UPDATE users SET referred_by = NULL WHERE referred_by = :uid"),
            text("DELETE FROM users WHERE id = :uid"),
        ]
        for q in queries:
            await session.execute(q, {"uid": user_id})
        await session.commit()
        print(f"✅ Foydalanuvchi ({user_id}) muvaffaqiyatli to'liq o'chirildi!")


async def delete_all_test_students():
    admin_ids = [int(a) for a in ADMINS if str(a).isdigit()]
    async with async_session() as session:
        print("🗑 Barcha test talabalari tozalanmoqda (Adminlar saqlanadi)...")
        queries = [
            text("DELETE FROM homework_submissions WHERE student_id NOT IN :admins"),
            text("DELETE FROM attendance WHERE student_id NOT IN :admins"),
            text("DELETE FROM test_results WHERE student_id NOT IN :admins"),
            text("DELETE FROM free_trial_requests WHERE student_id NOT IN :admins"),
            text("DELETE FROM enrollments WHERE student_id NOT IN :admins"),
            text("DELETE FROM support_chats WHERE student_id NOT IN :admins"),
            text("DELETE FROM payments WHERE student_id NOT IN :admins"),
            text("DELETE FROM referral_bonuses WHERE user_id NOT IN :admins"),
            text("UPDATE users SET referred_by = NULL WHERE id NOT IN :admins"),
            text("DELETE FROM users WHERE id NOT IN :admins"),
        ]
        for q in queries:
            await session.execute(q, {"admins": tuple(admin_ids)})
        await session.commit()
        print("✅ Barcha test o'quvchilari tozalandi!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Iltimos, Telegram ID kiriting: python clean_user.py <telegram_id>")
        print("Yoki barcha test akkauntlarini tozalash: python clean_user.py --all-students")
        sys.exit(1)

    arg = sys.argv[1]
    if arg == "--all-students":
        asyncio.run(delete_all_test_students())
    elif arg.isdigit():
        asyncio.run(delete_single_user(int(arg)))
    else:
        print("Noto'g'ri ID kiritildi.")
