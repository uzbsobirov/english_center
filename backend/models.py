"""
SQLAlchemy modellari.
TZ v2.6, 12-bo'lim (Database Modellari) va 7.5.1 bo'limi asosida.
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


class CourseTypeEnum(str, enum.Enum):
    IELTS = "IELTS"
    CEFR = "CEFR"
    General = "General"


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
    type: Mapped[CourseTypeEnum] = mapped_column(Enum(CourseTypeEnum), default=CourseTypeEnum.General)
    level: Mapped[LevelEnum] = mapped_column(Enum(LevelEnum))
    description: Mapped[dict] = mapped_column(JSON)
    duration_months: Mapped[int] = mapped_column(Integer)
    lessons_per_week: Mapped[int] = mapped_column(Integer, default=2)
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    price_per_lesson: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)  # TZ 12: Refund hisobi uchun
    image_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    @property
    def total_lessons(self) -> int:
        """Taxminiy jami darslar soni: oy x 4 hafta x haftalik dars soni."""
        return self.duration_months * 4 * self.lessons_per_week

    @property
    def effective_price_per_lesson(self) -> float:
        """Bir dars narxi - agar bazada kiritilmagan bo'lsa, umumiy narxdan hisoblanadi."""
        if self.price_per_lesson is not None and float(self.price_per_lesson) > 0:
            return float(self.price_per_lesson)
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
    max_students: Mapped[int] = mapped_column(Integer, default=12)
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
    shartli (atomik) UPDATE qilish orqali amalga oshiriladi.
    """
    __tablename__ = "free_trial_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    test_result_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    teacher_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    trial_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[FreeTrialStatusEnum] = mapped_column(
        Enum(FreeTrialStatusEnum), default=FreeTrialStatusEnum.pending
    )
    student_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)  # 1-5 yulduz
    student_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EnrollmentStatusEnum(str, enum.Enum):
    active = "active"
    waiting = "waiting"
    completed = "completed"
    dropped = "dropped"


class Enrollment(Base):
    """O'quvchining guruhga rasmiy yozilishi (to'lovdan keyin). TZ 12"""
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    free_trial_id: Mapped[int | None] = mapped_column(ForeignKey("free_trial_requests.id"), nullable=True)
    status: Mapped[EnrollmentStatusEnum] = mapped_column(
        Enum(EnrollmentStatusEnum), default=EnrollmentStatusEnum.active
    )
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
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
    refunded = "refunded"
    failed = "failed"


class Payment(Base):
    """TZ 12: to'lovlar jadvali."""
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enrollment_id: Mapped[int | None] = mapped_column(ForeignKey("enrollments.id"), nullable=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    discount_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    method: Mapped[PaymentMethodEnum] = mapped_column(Enum(PaymentMethodEnum))
    status: Mapped[PaymentStatusEnum] = mapped_column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.pending)
    confirmed_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    external_transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AttendanceStatusEnum(str, enum.Enum):
    present = "present"
    absent = "absent"
    late = "late"


class Attendance(Base):
    """TZ 7.3 & 9: Davomat jadvali."""
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    lesson_date: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[AttendanceStatusEnum] = mapped_column(Enum(AttendanceStatusEnum), default=AttendanceStatusEnum.present)
    marked_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Refund(Base):
    """TZ 9 & 12: qaytarish jarayoni."""
    __tablename__ = "refunds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("payments.id"), nullable=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    reason: Mapped[str] = mapped_column(Text)
    calculated_amount: Mapped[float] = mapped_column(Numeric(10, 2))  # formula bo'yicha avtomatik
    final_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending / approved / rejected
    approved_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Homework(Base):
    """TZ 7.4 & 12: Uy vazifalari."""
    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    teacher_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    lesson_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Telegram file_id
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WaitingList(Base):
    """TZ 6.2.1 & 12: guruh to'lganda kutish ro'yxati."""
    __tablename__ = "waiting_list"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"), nullable=True)
    level: Mapped[LevelEnum | None] = mapped_column(Enum(LevelEnum), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notified: Mapped[bool] = mapped_column(Boolean, default=False)


class GroupChangeRequest(Base):
    """TZ 6.3, 7.6 & 12: Guruhni o'zgartirish so'rovi."""
    __tablename__ = "group_change_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    current_group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    target_group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending / approved / rejected
    approved_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    balance_difference: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ReferralBonus(Base):
    """TZ 14.1 & 12: jamlanadigan foizli chegirma tizimi."""
    __tablename__ = "referral_bonuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))  # referrer_id
    referred_student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    bonus_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=5.0)
    applied_month: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending / applied
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TestSourceEnum(str, enum.Enum):
    manual = "manual"
    ai_pdf = "ai_pdf"


class Test(Base):
    """TZ 10, 12 va 7.5.1: Test Tizimi."""
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    teacher_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    certificate_type: Mapped[str] = mapped_column(String(20))  # IELTS / CEFR
    level: Mapped[LevelEnum] = mapped_column(Enum(LevelEnum))
    title: Mapped[dict] = mapped_column(JSON)  # {"uz": "...", "ru": "...", "en": "..."}
    passing_score: Mapped[float] = mapped_column(Numeric(5, 2), default=70.0)
    time_limit_min: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[TestSourceEnum] = mapped_column(Enum(TestSourceEnum), default=TestSourceEnum.manual)
    questions: Mapped[list] = mapped_column(JSON, default=list)  # tez yuklash uchun savollar kesh ro'yxati
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class QuestionTypeEnum(str, enum.Enum):
    mcq = "mcq"
    true_false = "true_false"
    fill_blank = "fill_blank"
    short_answer = "short_answer"
    translation = "translation"
    audio = "audio"


class Question(Base):
    """TZ 12 va 7.5.1: Test savollari (AI va Self-check bayroqlari bilan)."""
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
    order_num: Mapped[int] = mapped_column(Integer, default=1)
    type: Mapped[QuestionTypeEnum] = mapped_column(Enum(QuestionTypeEnum), default=QuestionTypeEnum.mcq)
    question: Mapped[dict] = mapped_column(JSON)  # {"uz": "...", "ru": "...", "en": "..."} yoki string
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)  # MCQ variantlar
    correct_answer: Mapped[str] = mapped_column(Text)
    audio_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=1)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)  # ⚠️ AI Self-check warning bayrog'i


class TestResult(Base):
    """TZ 12: Test natijalari."""
    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
    score: Mapped[float] = mapped_column(Numeric(5, 2))
    max_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    percent: Mapped[float] = mapped_column(Numeric(5, 2))
    passed: Mapped[bool] = mapped_column(Boolean)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answers: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CenterSetting(Base):
    """TZ 12 & 16.2: O'quv markazi sozlamalari va aloqa kontaktlari."""
    __tablename__ = "center_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contact_phone: Mapped[str] = mapped_column(String(20), default="+998901234567")
    contact_username: Mapped[str] = mapped_column(String(100), default="english_center_admin")
    address: Mapped[dict] = mapped_column(JSON, default=lambda: {
        "uz": "Toshkent sh., Amir Temur ko'chasi, 12-uy",
        "ru": "г. Ташкент, ул. Амира Темура, д. 12",
        "en": "12 Amir Temur street, Tashkent"
    })
    welcome_message: Mapped[dict | None] = mapped_column(JSON, default=lambda: {
        "uz": "Xush kelibsiz! Alpha English Center rasmiy botiga xush kelibsiz. Bu yerda siz kurslarga yozilishingiz, darajangizni aniqlash uchun test topshirishingiz va o'quv natijalaringizni kuzatishingiz mumkin.",
        "ru": "Добро пожаловать в официальный бот Alpha English Center! Здесь вы можете записаться на курсы, пройти тестирование для определения уровня и отслеживать успеваемость.",
        "en": "Welcome to the official Alpha English Center bot! Here you can enroll in courses, take placement tests, and track your academic progress."
    }, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SupportChatStatusEnum(str, enum.Enum):
    open = "open"
    closed = "closed"


class SupportChatClosedReasonEnum(str, enum.Enum):
    resolved = "resolved"
    timeout = "timeout"


class SupportChat(Base):
    """TZ 12 & 16.2: Jonli savol-javob (support) chatlari."""
    __tablename__ = "support_chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    admin_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    status: Mapped[SupportChatStatusEnum] = mapped_column(
        Enum(SupportChatStatusEnum), default=SupportChatStatusEnum.open
    )
    last_message_by: Mapped[str] = mapped_column(String(20), default="student")  # student / admin
    last_message_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_reason: Mapped[SupportChatClosedReasonEnum | None] = mapped_column(
        Enum(SupportChatClosedReasonEnum), nullable=True
    )


class UserBadge(Base):
    """TZ 15: Gamification badge'lari."""
    __tablename__ = "user_badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    badge_type: Mapped[str] = mapped_column(String(50))  # starter, top_student, regular, ambassador, etc.
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

