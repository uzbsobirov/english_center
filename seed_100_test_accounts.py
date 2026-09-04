"""
ALPHA LC — 100 ta sinov hisoblarini yaratish va bazani to'ldirish skripti.
Yaratiladi:
- 5 ta Teacher (O'qituvchi)
- 95 ta Student (O'quvchi)
- Referal zanjirlari va bonuslar
- Guruhga yozilishlar (Enrollments)
- To'lovlar (Payments - Payme, Click, Uzum, Naqd)
- Davomat yozuvlari (Attendance)
- Daraja test natijalari (TestResults A1-C2)
- Erishilgan nishonlar (UserBadges)
- Sinov darsi arizalari (FreeTrialRequests)
"""
import sys
import os
import random
from datetime import datetime, timedelta, date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import asyncio
from sqlalchemy import select, delete, text
from backend.database import async_session, engine
from backend.models import (
    User, RoleEnum, LanguageEnum, LevelEnum, Course, Group,
    Enrollment, EnrollmentStatusEnum, Payment, PaymentMethodEnum, PaymentStatusEnum,
    Attendance, AttendanceStatusEnum, Test, TestResult, FreeTrialRequest,
    FreeTrialStatusEnum, UserBadge, ReferralBonus
)

FIRST_NAMES_UZ = [
    "Jasur", "Bekzod", "Sardor", "Farrux", "Bobur", "Ulug'bek", "Otabek", "Doniyor",
    "Javohir", "Sherzod", "Sanjar", "Azizbek", "Shohruh", "Rustam", "Temur",
    "Madina", "Nilufar", "Zilola", "Kamola", "Feruza", "Gulnoza", "Shaxnoza",
    "Dildora", "Nodira", "Malika", "Zarina", "Rayhona", "Sevara", "Mohira", "Dilnoza"
]

LAST_NAMES_UZ = [
    "Karimov", "Aliyev", "Rahimov", "Tursunov", "Usmonov", "Normatov", "Xolmatov",
    "Qodirov", "Yo'ldoshev", "Saidov", "Nazarov", "Ergashev", "Bozorov", "Sobirov",
    "Karimova", "Aliyeva", "Rahimova", "Tursunova", "Usmonova", "Normatova", "Qodirova",
    "Yo'ldosheva", "Saidova", "Nazarova", "Ergasheva", "Bozorova", "Sobirova"
]

OPERATOR_CODES = ["90", "91", "93", "94", "95", "97", "98", "99", "88", "33"]
BADGE_TYPES = ["starter", "top_student", "regular", "ambassador", "streak_master", "quick_learner", "perfect_attendance"]


async def seed_100_accounts():
    print("=" * 65)
    print("🌱 100 TA SINOV HISOBINI YARATISH VA BAZANI BOYITISH BOSHLANDI...")
    print("=" * 65)

    # 1. DB jadval ustunlarini tekshirish
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE free_trial_requests ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;"))

    async with async_session() as session:
        # Mavjud guruhlar, kurslar va testlarni olish
        courses = (await session.execute(select(Course))).scalars().all()
        groups = (await session.execute(select(Group))).scalars().all()
        tests = (await session.execute(select(Test))).scalars().all()

        if not courses or not groups:
            print("⚠️ Kurslar yoki guruhlar topilmadi. Avval 'python init_db.py' ni bajaring.")
            return

        # Oldingi test hisoblarni tozalash (ID diapazoni: 7100000001 - 7100000100)
        test_ids = list(range(7100000001, 7100000101))
        print(f"🧹 Eski test hisoblar tekshirilmoqda va tozalanmoqda...")
        
        await session.execute(delete(ReferralBonus).where(ReferralBonus.user_id.in_(test_ids) | ReferralBonus.referred_student_id.in_(test_ids)))
        await session.execute(delete(UserBadge).where(UserBadge.user_id.in_(test_ids)))
        await session.execute(delete(TestResult).where(TestResult.student_id.in_(test_ids)))
        await session.execute(delete(Attendance).where(Attendance.student_id.in_(test_ids)))
        await session.execute(delete(Payment).where(Payment.student_id.in_(test_ids)))
        await session.execute(delete(Enrollment).where(Enrollment.student_id.in_(test_ids)))
        await session.execute(delete(FreeTrialRequest).where(FreeTrialRequest.student_id.in_(test_ids) | FreeTrialRequest.teacher_id.in_(test_ids)))
        await session.execute(delete(User).where(User.id.in_(test_ids)))
        await session.commit()

        print(f"✨ 100 ta hisob generatsiya qilinmoqda...")

        users_to_add = []
        created_student_ids = []
        created_teacher_ids = []

        # 5 ta O'qituvchi
        teacher_configs = [
            ("Jamshid Rahimov", "teacher_jamshid", LevelEnum.C1, LanguageEnum.uz),
            ("Shaxnoza Yusupova", "teacher_shaxnoza", LevelEnum.C1, LanguageEnum.ru),
            ("John Davis", "teacher_john", LevelEnum.C2, LanguageEnum.en),
            ("Dilnoza Alimova", "teacher_dilnoza", LevelEnum.B2, LanguageEnum.uz),
            ("Sardor Umarov", "teacher_sardor", LevelEnum.B2, LanguageEnum.uz),
        ]

        for i, (name, uname, lvl, lang) in enumerate(teacher_configs):
            tid = 7100000001 + i
            phone = f"+998{random.choice(OPERATOR_CODES)}{random.randint(1000000, 9999999)}"
            u = User(
                id=tid,
                full_name=name,
                username=uname,
                phone=phone,
                language=lang,
                role=RoleEnum.teacher,
                level=lvl,
                referral_code=f"TCH{100+i}",
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=random.randint(30, 90))
            )
            users_to_add.append(u)
            created_teacher_ids.append(tid)

        # 95 ta O'quvchi
        levels_pool = [LevelEnum.A1, LevelEnum.A2, LevelEnum.B1, LevelEnum.B2, LevelEnum.C1]
        langs_pool = [LanguageEnum.uz, LanguageEnum.uz, LanguageEnum.uz, LanguageEnum.ru, LanguageEnum.en]

        for i in range(5, 100):
            sid = 7100000001 + i
            fn = random.choice(FIRST_NAMES_UZ)
            ln = random.choice(LAST_NAMES_UZ)
            full_name = f"{fn} {ln}"
            uname = f"{fn.lower()}_{ln.lower()}_{i}"
            phone = f"+998{random.choice(OPERATOR_CODES)}{random.randint(1000000, 9999999)}"
            lvl = random.choice(levels_pool)
            lang = random.choice(langs_pool)

            # Ba'zi o'quvchilarda referer bo'ladi
            ref_by = None
            if created_student_ids and random.random() < 0.35:
                ref_by = random.choice(created_student_ids)

            u = User(
                id=sid,
                full_name=full_name,
                username=uname,
                phone=phone,
                language=lang,
                role=RoleEnum.student,
                level=lvl,
                referral_code=f"STU{1000+i}",
                referred_by=ref_by,
                referral_bonus_given=(ref_by is not None),
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=random.randint(5, 60))
            )
            users_to_add.append(u)
            created_student_ids.append(sid)

        session.add_all(users_to_add)
        await session.flush()
        print(f"✅ 100 ta foydalanuvchi yaratildi: 5 ta o'qituvchi, 95 ta o'quvchi.")

        # 3. Referal bonuslari yaratish
        referral_bonuses = []
        for u in users_to_add:
            if u.referred_by:
                bonus = ReferralBonus(
                    user_id=u.referred_by,
                    referred_student_id=u.id,
                    bonus_percent=5.0,
                    applied_month=date.today(),
                    status="applied" if random.random() < 0.5 else "pending",
                    is_used=random.random() < 0.3,
                    created_at=u.created_at
                )
                referral_bonuses.append(bonus)
        if referral_bonuses:
            session.add_all(referral_bonuses)
            print(f"✅ {len(referral_bonuses)} ta referal bonusi bog'landi.")

        # 4. Guruhlarga yozilishlar (Enrollments) va To'lovlar (Payments)
        enrollments = []
        payments = []
        attendances = []
        badges = []

        payment_methods = [PaymentMethodEnum.payme, PaymentMethodEnum.click, PaymentMethodEnum.uzum, PaymentMethodEnum.cash]

        for sid in created_student_ids:
            # 70% o'quvchi biror guruhga yozilgan
            if random.random() < 0.70:
                grp = random.choice(groups)
                status = random.choice([EnrollmentStatusEnum.active, EnrollmentStatusEnum.active, EnrollmentStatusEnum.active, EnrollmentStatusEnum.waiting, EnrollmentStatusEnum.completed])
                
                enr = Enrollment(
                    student_id=sid,
                    group_id=grp.id,
                    status=status,
                    enrolled_at=datetime.utcnow() - timedelta(days=random.randint(10, 40)),
                    is_active=(status == EnrollmentStatusEnum.active)
                )
                enrollments.append(enr)

        session.add_all(enrollments)
        await session.flush()
        print(f"✅ {len(enrollments)} ta guruhga yozilish (Enrollment) yaratildi.")

        # To'lovlar va Davomat
        for enr in enrollments:
            amt = random.choice([450000.0, 500000.0, 650000.0])
            discount = 25000.0 if random.random() < 0.3 else 0.0
            p_status = PaymentStatusEnum.confirmed if enr.status == EnrollmentStatusEnum.active else PaymentStatusEnum.pending
            
            pay = Payment(
                enrollment_id=enr.id,
                student_id=enr.student_id,
                group_id=enr.group_id,
                amount=amt - discount,
                discount_amount=discount,
                method=random.choice(payment_methods),
                status=p_status,
                confirmed_by=created_teacher_ids[0] if p_status == PaymentStatusEnum.confirmed else None,
                external_transaction_id=f"TX_{random.randint(10000000, 99999999)}",
                paid_at=datetime.utcnow() - timedelta(days=random.randint(1, 20)) if p_status == PaymentStatusEnum.confirmed else None,
                created_at=enr.enrolled_at
            )
            payments.append(pay)

            # Faol guruhlar uchun davomat belgilash (5 ta dars)
            if enr.status == EnrollmentStatusEnum.active:
                for lesson_idx in range(5):
                    l_date = date.today() - timedelta(days=(5 - lesson_idx) * 2)
                    att_status = random.choices(
                        [AttendanceStatusEnum.present, AttendanceStatusEnum.late, AttendanceStatusEnum.absent],
                        weights=[0.8, 0.1, 0.1]
                    )[0]
                    att = Attendance(
                        group_id=enr.group_id,
                        student_id=enr.student_id,
                        lesson_date=l_date,
                        status=att_status,
                        marked_by=created_teacher_ids[0],
                        created_at=datetime.combine(l_date, datetime.min.time())
                    )
                    attendances.append(att)

        session.add_all(payments)
        session.add_all(attendances)
        print(f"✅ {len(payments)} ta to'lov va {len(attendances)} ta davomat yozuvi yaratildi.")

        # 5. Test natijalari (TestResults)
        test_results = []
        for sid in created_student_ids:
            # 80% o'quvchi kamida bitta daraja testini yechgan
            if random.random() < 0.80 and tests:
                t = random.choice(tests)
                score = round(random.uniform(50.0, 100.0), 1)
                max_score = 100
                passed = score >= float(t.passing_score)
                duration = random.randint(180, 720)

                tr = TestResult(
                    student_id=sid,
                    test_id=t.id,
                    score=score,
                    max_score=max_score,
                    percent=score,
                    passed=passed,
                    duration_seconds=duration,
                    answers=[{"q": 1, "ans": "correct"}],
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                )
                test_results.append(tr)

                # Nishonlar (Badges)
                if passed and score >= 90:
                    badges.append(UserBadge(user_id=sid, badge_type="top_student"))
                if passed:
                    badges.append(UserBadge(user_id=sid, badge_type="starter"))
                if random.random() < 0.15:
                    badges.append(UserBadge(user_id=sid, badge_type="streak_master"))

        session.add_all(test_results)
        session.add_all(badges)
        print(f"✅ {len(test_results)} ta test natijasi va {len(badges)} ta nishon (badge) kiritildi.")

        # 6. Sinov darsi so'rovlari (FreeTrialRequest)
        trial_requests = []
        for sid in created_student_ids[:30]:  # Birinchi 30 ta o'quvchi uchun
            tr_status = random.choice([FreeTrialStatusEnum.pending, FreeTrialStatusEnum.invited, FreeTrialStatusEnum.attended])
            ft = FreeTrialRequest(
                student_id=sid,
                teacher_id=random.choice(created_teacher_ids) if tr_status != FreeTrialStatusEnum.pending else None,
                group_id=random.choice(groups).id if tr_status != FreeTrialStatusEnum.pending else None,
                trial_date=datetime.utcnow() + timedelta(days=random.randint(1, 3)) if tr_status == FreeTrialStatusEnum.invited else None,
                location="Auditoriya 101",
                status=tr_status,
                student_rating=random.randint(4, 5) if tr_status == FreeTrialStatusEnum.attended else None,
                student_feedback="Ajoyib dars bo'ldi!" if tr_status == FreeTrialStatusEnum.attended else None,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 10)),
                updated_at=datetime.utcnow()
            )
            trial_requests.append(ft)

        session.add_all(trial_requests)
        print(f"✅ {len(trial_requests)} ta FreeTrialRequest yozuvi yaratildi.")

        await session.commit()

    print("=" * 65)
    print("🎉 100 TA SINOV HISOB MUVAFFAQIYATLI YARATILDI VA BAZAGA JOYLANDI!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(seed_100_accounts())
