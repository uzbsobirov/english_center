# 🌟 ALPHA LC — O'quv Markazi Ekotizimi (Telegram Bot + WebApp + AI)

Zamonaviy o'quv markazlari uchun to'liq avtomatlashtirilgan boshqaruv ekotizimi: **Telegram Bot (Aiogram 3.x)**, **Telegram Mini App (React + Vite + Tailwind)**, **FastAPI Backend**, **PostgreSQL** va **AI PDF Test Generator**.

---

## 🚀 Asosiy Imkoniyatlar

### 🎓 1. O'quvchilar uchun
* **Ro'yxatdan o'tish & Profil:** 3 tilda (🇺🇿 uz, 🇷🇺 ru, 🇬🇧 en) ism, telefon va tilni sozlash.
* **Kurslar & Guruhlar Katalogi:** Barcha mavjud kurslar, dars jadvallari va o'qituvchilar ma'lumotlari.
* **Free Dars & Placement Test:** IELTS, CEFR va General English bo'yicha daraja testi (A1-C2).
* **To'lov Tizimi:** Free dars guruhiga moslashtirilgan to'lov, Naqd va Online (Click, Payme, Uzum).
* **Referal Dasturi:** Do'stlarni taklif qilish orqali +5% kümülyativ chegirma (100% gacha) va Ambassador nishoni.
* **Gamifikatsiya:** 7 ta maxsus badge, XP & Level, 7 kunlik Streak, Leaderboard va Kurs tamomlanganda avtomatik **PDF Sertifikat**.
* **Uy Vazifasi:** Joriy faol vazifani ajratib ko'rsatish, materiallarni yuklab olish va o'tmishdagi vazifalar tarixi.

### 👨‍🏫 2. O'qituvchilar va Adminlar uchun
* **Free Dars So'rovlari:** Yangi so'rovlar kelganda «✅ Qabul qilish» va «❌ Rad etish» (First-teacher-wins).
* **Davomat:** QR-kod orqali yoki botdan 1 ta bosishda guruh davomatini belgilash.
* **Uy Vazifasi Yuklash:** Guruhga fayl, rasm yoki izoh bilan uy vazifasi biriktirish.
* **To'lovlarni Tasdiqlash:** Naqd to'lovlarni qabul qilish va o'quvchini avtomatik guruhga yozish.
* **Admin Dashboard WebApp:** Jonli KPI statistika, guruhlar ochish/tahrirlash, o'quvchilar boshqaruvi, to'lovlar hisoboti.
* **🤖 AI PDF Test Generator:** PDF test faylidan AI orqali savollar, variantlar va javoblarni avtomatik ajratib olish va 1 ta bosishda faollashtirish.
* **📢 PRO Broadcast:** Barcha foydalanuvchilar, o'quvchilar yoki kurslar bo'yicha matn, rasm, video, hujjat yoki forward postlarni ommaviy tarqatish (ixtiyoriy inline tugma bilan).

---

## 🛠 Texnologiyalar

* **Backend:** Python 3.12, FastAPI, SQLAlchemy (Asyncio), Asyncpg, Pydantic, Alembic
* **Telegram Bot:** Aiogram 3.21, Fluent Runtime (aiogram-i18n)
* **Frontend:** React 19, Vite, TailwindCSS v4, Axios
* **Database:** PostgreSQL 16
* **AI & Generator:** Gemini API / OpenAI API / Regex Parser, PyPDF, ReportLab (PDF Certificates)
* **Deployment:** Docker, Docker Compose, Nginx, Cloudflare Tunnel

---

## 💻 Mahalliy Ishga Tushirish (Local Development)

### 1. Bog'liqliklarni o'rnatish
```powershell
# Virtual muhit yaratish
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Python paketlarini o'rnatish
pip install -r requirements.txt

# WebApp paketlarini o'rnatish
cd webapp
npm install
cd ..
```

### 2. .env faylini sozlash
`.env.example` dan nusxa olib `.env` yarating va `BOT_TOKEN`, `ADMINS`, `DB_PASS` larni kiriting:
```env
BOT_TOKEN=8976693690:AAH...
ADMINS=1435473812
DB_USER=postgres
DB_PASS=1234
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=english_center
WEBAPP_URL=http://localhost:5173
DEV_MODE=True
```

### 3. Ma'lumotlar bazasini initsializatsiya qilish
```powershell
python init_db.py --reset
```

### 4. Xizmatlarni ishga tushirish (4 ta terminalda)
```powershell
# Terminal 1: FastAPI Backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Vite WebApp Frontend
cd webapp
npm run dev

# Terminal 3: Telegram Bot & Scheduler
python main.py

# Terminal 4: Cloudflare Tunnel (Telegram Mini App uchun)
python tunnel.py
```

---

## 🐳 Production Serverga Joylashtirish (Docker)

Ubuntu VPS yoki istalgan Linux serverda 1 ta buyruq bilan ishga tushirish:

```bash
# 1. Loyihani klonlash
git clone https://github.com/uzbsobirov/english_center.git
cd english_center

# 2. .env faylini to'ldirish
cp .env.example .env
nano .env

# 3. 1-Click Deploy skriptini yurgazish
chmod +x deploy.sh
./deploy.sh
```

---

## 🧪 Avtomatlashtirilgan Testlar

```powershell
python scratch/test_stage4.py        # Davomat, Uy vazifasi va Eslatmalar
python scratch/test_stage6.py        # Gamifikatsiya, Nishonlar va PDF Sertifikat
python scratch/test_payments.py      # To'lovlar, Referal chegirmalari va Qaytarish
python scratch/test_free_trial_flow.py # Free Dars va O'qituvchi taklif oqimi
python scratch/test_ai_generator.py  # AI PDF Test Generator
```

---

## 👤 Muallif
* **ALPHA Learning Center Team**
* **Repository:** [uzbsobirov/english_center](https://github.com/uzbsobirov/english_center)
