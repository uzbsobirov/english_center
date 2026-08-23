"""
SQLAlchemy modellari.
TZ v2.4, 12-bo'lim (Database Modellari) asosida.
"""
import enum
from datetime import datetime, date
from sqlalchemy import (
    BigInteger, String, Boolean, DateTime, Date, ForeignKey,
    Enum, JSON, Integer, SmallInteger, Numeric, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class LanguageEnum(str, enum.Enum):
    uz = "uz"
    ru = "ru"
    en = "en"


class RoleEnum(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    manager = "manager"
    admin = "admin"


class LevelEnum(str, enum.Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user ID
    full_name: Mapped[str] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[LanguageEnum] = mapped_column(Enum(LanguageEnum), default=LanguageEnum.uz)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.student)
    level: Mapped[LevelEnum | None] = mapped_column(Enum(LevelEnum), nullable=True)
    referral_code: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    referred_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    referral_bonus_given: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[dict] = mapped_column(JSON)  # {"uz": "...", "ru": "...", "en": "..."}
    type: Mapped[str] = mapped_column(String(20))  # IELTS / CEFR / General
    level: Mapped[LevelEnum] = mapped_column(Enum(LevelEnum))
    description: Mapped[dict] = mapped_column(JSON)
    duration_months: Mapped[int] = mapped_column(Integer)
    lessons_per_week: Mapped[int] = mapped_column(Integer, default=2)
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    image_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    @property
    def total_lessons(self) -> int:
        """Taxminiy jami darslar soni: oy x 4 hafta x haftalik dars soni."""
        return self.duration_months * 4 * self.lessons_per_week

    @property
    def price_per_lesson(self) -> float:
        """Bir dars narxi - qo'lda kiritilmaydi, umumiy narx va dars sonidan avtomatik hisoblanadi."""
        total = self.total_lessons
        if total <= 0:
            return 0.0
        return float(self.price) / total



class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    teacher_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100))
    schedule: Mapped[list] = mapped_column(JSON)  # [{"day": 1, "time": "18:00"}, ...]
    room: Mapped[str | None] = mapped_column(String(100), nullable=True)
    group_chat_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    max_students: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    zoom_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class FreeTrialStatusEnum(str, enum.Enum):
    pending = "pending"
    invited = "invited"
    attended = "attended"
    declined = "declined"
    enrolled = "enrolled"


class FreeTrialRequest(Base):
    """
    6.1.1 / 6.2 / 7.1.1 bo'limlari: free dars so'rovi.
    'Birinchi bosgan g'olib' mexanizmi shu jadvalning status maydoniga
    shartli (atomik) UPDATE qilish orqali amalga oshiriladi (services/ da yoziladi).
    """
    __tablename__ = "free_trial_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    test_result_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # keyin test_results bilan bog'lanadi
    teacher_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    trial_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[FreeTrialStatusEnum] = mapped_column(
        Enum(FreeTrialStatusEnum), default=FreeTrialStatusEnum.pending
    )
    student_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)  # 1-5
    student_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)




class Enrollment(Base):
    """O'quvchining guruhga rasmiy yozilishi (to'lovdan keyin)."""
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PaymentMethodEnum(str, enum.Enum):
    payme = "payme"
    click = "click"
    uzum = "uzum"
    cash = "cash"


class PaymentStatusEnum(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    method: Mapped[PaymentMethodEnum] = mapped_column(Enum(PaymentMethodEnum))
    status: Mapped[PaymentStatusEnum] = mapped_column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.pending)
    confirmed_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)  # naqd bo'lsa o'qituvchi/admin
    external_transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Payme/Click/Uzum ID
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Refund(Base):
    """9-bo'lim: qaytarish jarayoni."""
    __tablename__ = "refunds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    reason: Mapped[str] = mapped_column(Text)
    calculated_amount: Mapped[float] = mapped_column(Numeric(10, 2))  # formula bo'yicha avtomatik
    final_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)  # admin tasdiqlagan/o'zgartirgan
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/approved/rejected
    approved_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Homework(Base):
    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    teacher_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Telegram file_id
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WaitingList(Base):
    """6.2.1: guruh to'lgan holatda, boshqa guruh ham topilmasa shu yerga tushadi."""
    __tablename__ = "waiting_list"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    level: Mapped[LevelEnum] = mapped_column(Enum(LevelEnum))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReferralBonus(Base):
    """14.1: jamlanadigan foizli chegirma tizimi."""
    __tablename__ = "referral_bonuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))  # bonus oluvchi
    referred_student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))  # taklif qilingan o'quvchi
    percent: Mapped[float] = mapped_column(Numeric(5, 2))
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)



class Test(Base):
    """10-bo'lim: Test Tizimi. O'qituvchi Web App orqali yaratadi (7.5)."""
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    certificate_type: Mapped[str] = mapped_column(String(20))  # IELTS / CEFR
    level: Mapped[LevelEnum] = mapped_column(Enum(LevelEnum))
    title: Mapped[dict] = mapped_column(JSON)  # {"uz": "...", "ru": "...", "en": "..."}
    passing_score: Mapped[float] = mapped_column(Numeric(5, 2))  # 6.1.1: o'tish bali
    questions: Mapped[list] = mapped_column(JSON)  # savollar: MCQ/fill-in/tarjima/audio
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
    score: Mapped[float] = mapped_column(Numeric(5, 2))  # olingan ball
    percent: Mapped[float] = mapped_column(Numeric(5, 2))  # foiz
    passed: Mapped[bool] = mapped_column(Boolean)  # passing_score dan yuqorimi
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answers: Mapped[list] = mapped_column(JSON)  # har savol uchun javob va to'g'ri/noto'g'ri
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)