# 📋 English Center Telegram Bot & WebApp — O'zgarishlar va Bajarilgan Ishlar Hisoboti

Ushbu hujjatda **English Center** loyihasining texnik topshiriq (TZ v2.6) talablari asosida to'liq qayta ko'rib chiqilgan, yaratilgan va modernizatsiya qilingan barcha modullari, fayllari va imkoniyatlari jamlangan.

---

## 1. 🤖 Telegram Bot (Foydalanuvchi & O'qituvchi/Admin Menyulari)

### 📢 Multimedia Xabar Yuborish (Broadcast)
- **Fayl:** `app/handlers/teachers/broadcast.py` *(Yangi)*
- **Tavsif:** Adminlar va o'qituvchilar uchun qulay, ko'p funksiyali ommaviy xabarnoma tizimi yaratildi:
  - **Auditoriyani nishonga olish:** Barchaga / Faqat talabalarga / Faqat o'qituvchilarga / Faqat IELTS yoki CEFR o'quvchilariga.
  - **Multimedia qo'llab-quvvatlash:** Oddiy matn, rasmlar, videolar, fayl/hujjatlar va kanallardan forward qilingan postlarni nusxalab yuborish.
  - **Inline Tugmalar:** Xabar ostiga ixtiyoriy formatda tashqi havola tugmalari (`Tugma matni | https://...`) qo'shish imkoniyati.
  - **Telegram Rate Limiting:** Sekundiga 30 ta xabar yuborish chegarasi (Telegram Flood control) bilan xavfsiz parallel uzatish.

### ⚙️ «Sozlamalar», Guruhni O'zgartirish va Pulni Qaytarish (Refund)
- **Fayllar:** `app/handlers/users/settings.py` *(Yangi)*, `app/handlers/teachers/requests_approval.py` *(Yangi)*, `app/keyboards/main_menu.py`, `locales/{uz,ru,en}/LC_MESSAGES/bot.ftl`
- **Tavsif:**
  - Asosiy menyuda **«⚙️ Sozlamalar»** bo'limi yaratildi.
  - **Tilni o'zgartirish:** O'zbek, Rus va Ingliz tillarini bir zumda almashtirish.
  - **Telefon raqamni yangilash:** Kontaktni qayta yuborish.
  - **Guruh almashtirish so'rovi:** Talaba o'z guruhidan boshqa guruhga o'tish sababini kiritib so'rov yuboradi. Admin/O'qituvchi tugma orqali tasdiqlasa, talaba avtomatik yangi guruhga o'tkaziladi.
  - **Pulni qaytarish (Refund):** Kursdan ketish va qolgan mablag'ni qaytarib olish so'rovi. Tizim avtomatik quyidagi formula bo'yicha hisoblaydi:
    $$\text{Qaytariladigan summa} = \text{To'langan summa} - (\text{Qatnashgan darslar soni} \times \text{1 dars narxi})$$
  - Admin tasdiqlashi bilan o'quvchi guruhdan chiqariladi, to'lov holati `refunded` ga o'tadi va barcha tomonlarga bildirishnoma boradi.

### 🟢 Bepul Sinov Darsi Davomati va 1-5 Yulduzli Baholash
- **Fayl:** `app/handlers/teachers/trial_requests.py`
- **Tavsif:**
  - O'qituvchi bepul dars so'rovini qabul qilgach, dars kuni unga **«🟢 Darsga Keldi»** va **«🔴 Kelmadi»** tugmalari taqdim etiladi.
  - O'quvchi darsga kelganida, unga Telegram orqali **1 dan 5 gacha baholash (⭐ 1-5)** taklifi yuboriladi.
  - Baholashdan so'ng, tizim talabaga rasmiy guruhga a'zo bo'lish (to'lov qilish) havolasini taqdim etadi.

### 📊 O'quvchi Progressi (Statistika & Gamifikatsiya)
- **Fayllar:** `app/handlers/users/progress.py` *(Yangi)*, `backend/api/routes/student.py`, `webapp/src/pages/StudentProgress.jsx` *(Yangi)*
- **Tavsif:**
  - Botda **«📊 Progress»** tugmasi orqali o'quvchining to'liq statistikasi chiqariladi:
    - **Davomat intizomi:** Foiz va progress bar ko'rinishida (`[🟩🟩🟩🟩⬜️⬜️⬜️⬜️⬜️⬜️] 92.5% (18/20 dars)`).
    - **Test natijalari:** Topshirilgan testlar soni va o'rtacha ball.
    - **Uy vazifalari:** Topshirilgan uy vazifalari miqdori.
    - **Yutuqlar (Badges):** 🌱 Starter, ⚡️ Regular, 🏆 Master, 📚 Homework Hero, 👥 Ambassador.
  - **Web App:** «📱 Batafsil grafiklar» tugmasi orqali interaktiv Mini App sahifasida to'liq tahlil va unvonlar kartalari taqdim etiladi.

### 🎯 General English Yo'nalishi
- **Fayllar:** `app/handlers/users/free_lesson.py`, `webapp/src/pages/TestPage.jsx`
- **Tavsif:** IELTS va CEFR qatoriga **General English** yo'nalishi to'liq integratsiya qilindi.

---

## 2. ⚙️ Backend & Ma'lumotlar Bazasi (FastAPI & PostgreSQL)

### 💳 Click & Payme Real Webhook Integratsiyasi
- **Fayl:** `backend/api/routes/payments.py` *(Yangi)*, `backend/main.py`
- **Tavsif:**
  - **Click Webhook:** `/api/payments/click/prepare` va `/api/payments/click/complete` (MD5 imzo tekshiruvi, to'lov summasi validatsiyasi).
  - **Payme Webhook:** `/api/payments/payme` (JSON-RPC 2.0 protokoli: `CheckPerformTransaction`, `CreateTransaction`, `PerformTransaction`, `CheckTransaction`).
  - **Avtomatlashtirish:** To'lov muvaffaqiyatli yakunlanishi bilan o'quvchiga avtomatik `Enrollment` (guruh a'zoligi) beriladi, Telegram orqali chek yuboriladi va taklif qilgan do'stiga **+5% doimiy keshbek bonusi** yoziladi.
  - **To'lov havolalari:** Click va Payme ilovalarida to'g'ridan-to'g'ri to'lash uchun Checkout URL generatori yaratildi.

### 📊 Dashboard O'quvchilar Statistikasi Filtrlash
- **Fayl:** `backend/api/routes/admin.py`
- **Tavsif:**
  - Admin/O'qituvchilar test maqsadida guruhlarga a'zo bo'lganda ular o'quvchilar soniga (`+1`) qo'shilib ketmasligi ta'minlandi. Faqat `role == student` bo'lgan haqiqiy talabalar hisoblanadi.

### 📥 Excel (.CSV) Formatda Hisobotlarni Yuklab Olish
- **Fayl:** `backend/api/routes/admin.py`
- **Tavsif:**
  - `/api/admin/export/payments-csv` — To'lovlar ro'yxatini to'liq tafsilotlari (summa, sana, usul, talaba, guruh) bilan Excel formatida yuklash.
  - `/api/admin/export/students-csv` — O'quvchilar ro'yxatini telefon raqami, username va tillari bilan Excel formatida yuklash.

### ⏳ 24 Soatlik Test Retake Cooldown va 1 Daraja Pastga Tavsiya
- **Fayl:** `backend/api/routes/tests.py`
- **Tavsif:**
  - Testdan o'ta olmagan o'quvchi xuddi shu darajani 24 soat ichida qayta topshira olmaydi (cooldown).
  - Tizim unga darhol **1 daraja pastroq** darajadagi testni (masalan, B2 -> B1, B1 -> A2) topshirishni tavsiya qiladi.

### 🧠 Kuchaytirilgan AI PDF Test Generatori
- **Fayl:** `backend/services/ai_test_generator.py`
- **Tavsif:**
  - Har qanday formatdagi savol raqamlari (`1.`, `Q1:`, `Question 1:`, `(1)`) va variantlar (`A)`, `(A)`, `A.`, `a)`) aniq ajratiladi.
  - PDF hujjat oxiridagi **«Answer Key» (To'g'ri javoblar jadvali)** avtomatik o'qib olinadi va savollarga to'g'ri javob qilib bog'lanadi.

### ⏰ Avtomatlashtirilgan Eslatmalar va Eskalatsiya
- **Fayl:** `backend/services/scheduler.py`
- **Tavsif:**
  - **15 daqiqalik support chat timeouti:** 15 daqiqa javobsiz qolgan muloqotlar avtomatik yopiladi.
  - **3 soatlik uy vazifasi eslatmasi:** Dars tugagach 3 soat ichida uy vazifasi kiritilmasa, o'qituvchiga eslatma, kiritilmasa bosh adminga eskalatsiya yuboriladi.

---

## 3. 💻 Mini WebApp (React & Tailwind CSS)

### 🎨 Test topshirish sahifasi
- **Fayl:** `webapp/src/pages/TestPage.jsx`
- **Tavsif:**
  - **General English** tanlovi qo'shildi.
  - 24 soatlik cheklov (cooldown) bo'lganda, foydalanuvchiga qolgan vaqt ko'rsatiladi va to'g'ridan-to'g'ri 1 daraja past testni boshlash tugmasi chiqadi.

### 🖥 Admin Dashboard
- **Fayl:** `webapp/src/pages/AdminDashboard.jsx`
- **Tavsif:**
  - O'quvchilar va To'lovlar bo'limiga **«📥 Excel Eksport»** tugmalari o'rnatildi.
  - Kurslar va guruhlarni boshqarish interfeysi mukammallashtirildi.

---

## 4. 🐳 Serverga O'rnatish & DevOps Suite

| Fayl | Maqsadi |
| :--- | :--- |
| `Dockerfile` | Python 3.12 FastAPI backend va Aiogram bot konteyneri. |
| `webapp/Dockerfile` | Vite React frontendni yig'uvchi va Nginx da tarqatuvchi konteyner. |
| `webapp/nginx.conf` | Frontend SPA routing va statik fayllarni tarqatish konfiguratsiyasi. |
| `nginx/nginx.conf` | Tashqi Nginx Reverse Proxy (SSL, Gzip, API va WebApp marshrutlash). |
| `docker-compose.yml` | PostgreSQL 16, Backend, Bot, WebApp va Nginx ni bitta tizim sifatida ishga tushirish. |
| `deploy.sh` | Linux Ubuntu/Debian serverlarida 1 ta buyruq bilan o'rnatish skripti. |
| `.env.example` | Barcha kerakli muhit o'zgaruvchilari namunasi. |
| `README.md` | Serverga to'liq o'rnatish va sozlash bo'yicha batafsil qo'llanma. |

---

---

## 6. 🚀 Eng So'nggi Yangilanishlar (v2.6.5 — 2026-09-01)

### 🛡 Ro'yxatdan O'tish & Kontakt Xavfsizligi
- Ro'yxatdan o'tishda faqat o'z Telegram akkauntiga tegishli raqam (`message.contact.user_id == message.from_user.id`) qabul qilinadi.
- Forward qilingan kontaktlar va qo'lda soxta raqam yozish butunlay taqiqlandi.
- `.env` dagi `ADMINS=1435473812` foydalanuvchisi ro'yxatdan o'tishi bilan unga avtomatik tarzda `RoleEnum.admin` beriladi.
- Soxta `+998901112233` raqami bazadan tozalandi (`phone=None`).

### 🎯 Sinov Darslari Davomati (Free Trial UX)
- «👥 Davomat olish» ichiga **«🎯 Sinov darslari davomati»** ro'yxati qo'shildi. O'qituvchi o'quvchi kartasini ochib bitta bosishda `[🟢 Darsga Keldi]` yoki `[🔴 Kelmadi]` belgilashi mumkin.
- Darsdan 2 soat o'tgach, davomat belgilanmagan bo'lsa, `scheduler.py` o'qituvchiga to'g'ridan-to'g'ri yangi eslatma yuboradi.
- O'quvchi darsni baholagach chiqqan `[💳 Rasmiy guruhga to'lov qilish]` (`start_payment_flow`) callback handler ulandi.

### 📢 Broadcast: Forward & @postbot
- `@postbot` orqali yaratilgan barcha inline tugmalar to'liq saqlanadi va yetkaziladi.
- Kanallardan forward qilingan postlarni asl nusxada (`bot.forward_message`) yoki toza nusxa (`bot.copy_message`) sifatida tarqatish rejimlari qo'shildi.

### 🛠 AI Test Builder & Test Boshqaruvi
- Test topshirishda `GET /api/tests/by-level/{level}` so'rovi `.order_by(Test.created_at.desc())` qoidasi bilan yangilandi. Eng yangi yuklangan testlar darhol o'quvchi sahifasida chiqadi.
- `TestBuilder.jsx` da mavjud barcha testlarni ko'rish, savollarini tahrirlash (`PUT /api/teacher/tests/{id}`) va muvaffaqiyatli saqlash banneri qo'shildi.

### 👨‍🏫 O'qituvchilarni Qo'shish va Boshqarish Tizimi
- **Web App Admin Dashboard:** Yangi **«👨‍🏫 O'qituvchilar»** bo'limi yaratildi. Admin o'qituvchilar ro'yxatini, biriktirilgan guruhlarini ko'rishi, `[➕ Yangi O'qituvchi Qo'shish]` modali orqali yangi o'qituvchi tayinlashi yoki `[🗑 O'chirish]` orqali vazifasidan ozod qilishi mumkin.
- **Backend API:** `GET /api/admin/teachers`, `POST /api/admin/teachers`, `DELETE /api/admin/teachers/{teacher_id}` endpointlari joriy etildi.
- **Telegram Bot Buyruqlari:** 
  - `/add_teacher [TELEGRAM_ID] [Ism Familiya]` — Istalgan foydalanuvchiga bir zumda O'qituvchi (Teacher) rolini beradi va unga bildirishnoma yuboradi.
  - `/teachers` — Mavjud barcha o'qituvchilar ro'yxatini ko'rish.
  - `/remove_teacher [TELEGRAM_ID]` — O'qituvchini o'quvchi roliga tushirish.
- **Guruhlarga biriktirish:** Yangi guruh ochish yoki tahrirlashda o'qituvchilar ro'yxati avtomatik shakllanadi.

### ⏰ Uy Vazifasi Eslatmalari Vaqtini Dars Jadvaliga Bog'lash
- `backend/services/scheduler.py` yangilandi:
  - Faqat **bugun dars kuni bo'lgan** guruhlarni tekshiradi.
  - Guruhning dars boshlanish vaqti (`16:00`, `18:00` va h.k.) + davomiyligi (90-120 daqiqa) hisoblanib, **dars tugaganidan roppa-rosa 3 soat o'tganidagina** eslatma yuboriladi.
  - Yangi yaratilgan yoki bugun darsi bo'lmagan guruhlar uchun noto'g'ri xabarlar ketishi butunlay to'xtatildi.

### 🗓 Guruh Ochishda Dars Kunlarini Tanlash (Schedule Days Selector)
- Guruh qo'shish va tahrirlashda haftaning istalgan kunlarini alohida tanlash (`Dush`, `Sesh`, `Chor`, `Pay`, `Jum`, `Shan`, `Yak`) va tezkor andozalar (`Toq kunlar`, `Juft kunlar`, `Har kuni`, `Dam olish`) qo'shildi.

### 🔍 Test Natijalarida Xatolar Tahlili (Test Question Review)
- Test yakunlangach, barcha savollar bo'yicha to'g'ri va xato javoblarning batafsil tahlili chiqadi.
- Filter orqali faqat xatolarni (`❌ Xatolar`) yoki faqat to'g'ri javoblarni (`✅ To'g'ri`) ajratib ko'rish mumkin.
- O'quvchi o'zi belgilagan variant bilan bir qatorda haqiqiy to'g'ri variantni yorqin vizual belgilar bilan ko'radi.

### 🔗 Guruh Telegram Chat Havolasi & Profil
- Guruh yaratishda `🔗 Guruh Telegram Chat Havolasi` kiritish maydoni qo'shildi. O'quvchi to'lov qilib guruhga qo'shilgach, «👤 Profilim» menyusida o'z guruhining Telegram chatiga ulanish tugmasi chiqadi.

### ⚙️ Markaz Kontakt Sozlamalari Boshqaruvi
- Botdagi «📞 Bog'lanish» ma'lumotlari to'liq `center_settings` ma'lumotlar bazasidan olinadi.
- Admin WebApp panelida yangi **«⚙️ Sozlamalar»** tab yaratildi. Admin telefon, username va manzillarni o'zgartirishi bilan botda darhol yangilanadi.

### 💰 Refund Jarayonida Guruhdan Avtomatik Chiqarish
- Refund tasdiqlanganda o'quvchining guruhga yozilishi avtomatik `dropped` va `is_active=False` qilinadi.
- To'lov holati `refunded` ga o'tkazilib, talabaga rasmiy ogohlantirish xabari boradi.
- Admin WebApp To'lovlar ro'yxatida **`[💰 Refund]`** tugmasi orqali to'lovni bir bosishda qaytarish imkoniyati qo'shildi.

### 🔒 Support Muloqot Yopilishi va Timeout Muammosi Yechimi
- Bir xil o'quvchi bir nechta xabar yuborganda ortiqcha parallel `SupportChat` qatorlari ochilmaydi.
- Admin muloqotni yopganda barcha ochiq qatorlar to'liq `resolved` qilinadi va 15 daqiqalik scheduler asossiz xabar yubormaydi.

### 📖 Uyga Vazifa Qo'shilganda Guruh O'quvchilariga Xabarnoma
- O'qituvchi yoki Admin uy vazifasini qo'shganda, o'sha guruhdagi barcha o'quvchilarga og'ir fayllarsiz toza matnli bildirishnoma («📖 UYGA VAZIFA YUKLANDI! ..., botning Uyga vazifa bo'limini tekshiring») va **`[📋 Uyga vazifani tekshirish]`** tugmasi boradi. O'quvchi xohlasa tugmani bosib, vazifa bo'limidan fayllarni yuklab oladi.

### 🎯 3 Bosqichli Qat'iy Rol Matritsasi (Faqat Ustoz, Faqat Admin, Ham Admin / Ham Ustoz)
- **Faqat O'qituvchi:** Faqat Ustoz Kabineti (`TeacherDashboard`) ko'rinadi. Sozlamalar va moliyaviy ma'lumotlar yo'q.
- **Faqat Admin:** Faqat Admin Dashboard (`AdminDashboard`) ko'rinadi. O'qituvchilikka oid ortiqcha tugmalar yo'q.
- **Ham Admin, Ham Ustoz:** Ikkala sahifaga ham to'liq va oson kirish (Admin ichida `👨‍🏫 Mening Darslarim` vkladkasi va `[ 👨‍🏫 Ustoz Kabineti ]` tugmasi mavjud).

### 🧪 100% Tizim Testi va Test Submishin Xatosi Tuzatildi
- `backend/api/routes/tests.py` da test javoblari tahlilida `import re` ulanmaganligi tuzatildi.
- Barcha CEFR darajalari (A1 dan C2 gacha) rasmiy placement testlari bilan to'ldirildi.
- `test_suite.py` (11/11 — 100%), `master_verification.py` (10/10 — 100%) va `test_student_full_journey.py` to'liq muvaffaqiyat bilan yakunlandi.

### 👨‍🏫 Maxsus O'qituvchi Kabineti va Qat'iy Rol Ajratish
- **O'qituvchi Sahifasi:** Hech qanday sozlamalar (`⚙️ Sozlamalar`), moliyaviy hisobotlar yoki switcher tugmalari ko'rsatilmaydi. Faqat o'qituvchining darslari, o'quvchilari va testlari ko'rinadi.
- **Telegram Bot Menyusi:** O'qituvchi uchun to'g'ridan-to'g'ri `👨‍🏫 O'qituvchi Kabineti` tugmasi qo'shildi.

### 👥 Xodimlar: O'qituvchilar va Adminlarni Bir Qatorda Boshqarish (Web App & Bot)
- **Web App Admin Dashboard:** `👨‍🏫 O'qituvchilar` vkladkasi bilan bir qatorda **`👑 Adminlar`** vkladkasi va modali yaratildi (`➕ Yangi Admin Qo'shish`, `🗑 O'chirish`).
- **Telegram Bot Admin Menyu:** Bot klaviaturasiga `👨‍🏫 O'qituvchilar` va `👑 Adminlar` tugmalari qatori kiritildi.
- **Xush Kelibsiz Matni Yangilandi:** Botdagi `/admin` xush kelibsiz xabari va WebApp'dagi asosiy banner yangilanib, barcha yangi vositalar ro'yxati keltirildi.

### 🛡 Qaytarish (Refund) va Guruh Almashtirishda Tugmalar Bosilishi Xatosi Tuzatildi
- **Tugma Nomini Sabab Qilib Olish Muammosi Bartaraf Etildi:** Refund yoki Guruh almashtirishda `👑 Admin Panel` yoki boshqa menyu tugmasi bosilganda, u sabab sifatida qabul qilinmaydi; aksincha, so'rov bekor qilinib, foydalanuvchi bosgan menyuga to'g'ri o'tadi.
- **Bekor Qilish Inline Tugmasi:** Ikkala jarayonga ham `[❌ Bekor qilish]` tugmasi kiritildi.
- **Validatsiya:** Sabab kamida 5 ta belgidan iborat bo'lishi talab qilinadi.

### 📝 AI va Qo'lda Test Yaratishda Barcha Turdagi Savollar va PDF Layout
- **Passage Biriktirish:** Agar o'qish matni (Reading passage) bir nechta savolga tegishli bo'lsa, o'sha matn barcha tegishli savollarning har biriga biriktiriladi.
- **Qog'oz Chiziqlarini Tozalash:** Qog'ozdagi testlarda ochiq savoldan keyingi qo'lda yozish chiziqlari (`________________`) savol matnidan butunlay tozalanadi va toza `short_answer` sifatida shakllanadi.
- **To'liq Shart va Matn Saqlanishi:** Topshiriq ko'rsatmalari (*«Choose NO MORE THAN TWO WORDS»*) savol matni bilan birga o'quvchiga taqdim etiladi.
- **Google Gemini AI & 100K Matn:** `.env` ga ulangan Google Gemini AI modeli 100,000 belgili katta PDF'larni ham uzib qo'ymasdan, to'liq hajmda professional tahlil qiladi.
- **PDF Layout Tahlili:** 2 ustunli testlar, jadvallar va uzilib qolgan qatorlar layout rejimi orqali to'g'ri o'qiladi, javoblar kaliti esa asosiy savollardan avtomatik qirqib olinadi.
- **Choice Yo'q Savollar:** PDF'dan AI orqali test tuzishda variantlarsiz bo'lgan barcha savollar (**True/False**, **Bo'sh joyni to'ldirish**, **Ochiq qisqa savollar**) to'liq ajratib olinadi.
- **Ko'p Turdagi Savollar Builderi:** O'qituvchi Test Builderda savol yaratishda `[🔘 Variantli]`, `[⚖️ True/False]`, `[✍️ Bo'sh joy]`, `[📝 Ochiq savol]` turlarini erkin tanlab, variantlar qo'shishi/o'chirishi va to'g'ri javoblarni matn shaklida kiritishi mumkin.
- **Interaktiv Test Ishlash & Tekshirish:** O'quvchi har bir savol turiga mos tarzda javob belgilaydi yoki matn kiritadi; baholash tizimi sinonim javoblarni va katta-kichik harflarni to'g'ri tekshiradi.

### 💳 To'lov Tasdiqlashdagi Xatolik Tuzatildi
- Online va naqd to'lovni tasdiqlashda sessiya yopilgandan so'ng yuzaga kelishi mumkin bo'lgan barcha xatoliklar to'liq bartaraf etildi.
- To'lov tasdiqlanishi bilan yuboriladigan tabrik xabarining o'zida **`[👥 Guruh Telegram Chati]`** havolasi to'g'ridan-to'g'ri taqdim etiladi.

### 🔄 UX & Barqarorlik Yaxshilanishlari
- **Test Oxirgi Savoli:** Ekrandagi pastki suzuvchi tugma oxirgi savol variantlarini yopib qo'ymasligi uchun sahifa pastki paddingi va maxsus spacer qo'shildi. Barcha savollar 4 ta to'liq (`A, B, C, D`) variantga keltirildi.
- **Toza Tahrirlash:** Baholashdan so'ng to'lov tugmasi bosilganda eski xabar tozalanib, to'g'ridan-to'g'ri to'lov kartasiga aylanadi.
- **RoleEnum xatosi:** Referal orqali ro'yxatdan o'tishdagi import xatosi to'liq tuzatildi.

### 🎨 Dark Glassmorphism Luxury Dizayni
- `AdminDashboard.jsx` va `TestBuilder.jsx` kiber-estetik dark glassmorphism dizayniga to'liq o'tkazildi.

---
*Hisobot so'nggi yangilangan sana: 2026-yil 1-sentyabr*
