# 📋 CHANGELOG — English Center Bot & WebApp

Barcha o'zgarishlar, yangilanishlar, xavfsizlik yaxshilanishlari va yangi modullar xronologiyasi.

---

## 🚀 [2026-09-04] — Test Tizimi, Bug Fixes & Full Lifecycle Testing (v2.6.6)

### 1. 🐞 Scheduler & FreeTrialRequest Xatoligi Bartaraf Etildi
- **`updated_at` Ustuni:** `backend/models.py` dagi `FreeTrialRequest` modeliga va PostgreSQL bazasidagi `free_trial_requests` jadvaliga `updated_at` ustuni qo'shildi (`DEFAULT CURRENT_TIMESTAMP`).
- **Scheduler crash tuzatildi:** `backend/services/scheduler.py` dagi `check_trial_attendance_reminders` funksiyasida `FreeTrialRequest has no attribute 'updated_at'` sababli yuzaga kelgan bot polling to'xtab qolish xatosi butunlay tuzatildi.

---

### 2. 🧪 100 Ta Haqiqiy Sinov Hisoblari Generatori (`seed_100_test_accounts.py`)
- **Taqsimot:** 5 ta O'qituvchi (Teachers) va 95 ta O'quvchi (Students) hisoblari yaratildi (`7100000001` – `7100000100`).
- **Real ma'lumotlar:** Haqiqiy o'zbek/rus/ingliz ism-familiyalari, O'zbekiston operatorlari telefon raqamlari (+99890/91/93/94/97/99/33), tillar (`uz`, `ru`, `en`) va darajalar (`A1`–`C2`).
- **Bog'langan modullar:** 34 ta referal zanjiri va bonusi, 64 ta guruhga a'zolik (Enrollment), 64 ta to'lov (Payme, Click, Uzum, Cash), 215 ta dars davomati, 81 ta test natijalari, 101 ta gamifikatsiya nishonlari (Badges) va 30 ta Free Trial arizalari yaratildi.

---

### 3. 🎯 Test Tizimi Javob Tekshiruvi Bug Fixi (`backend/api/routes/tests.py`)
- **To'g'ri javoblar kaliti moslashtirildi:** A2, B1, B2, C1, C2 testlarida to'g'ri javoblar kaliti `"correct"`, A1 da esa `"correct_answer"` bo'lganligi sababli `_is_answer_correct` funksiyasi barcha A2–C2 testlarini 0 ball (0%) qilib baholayotgan edi.
- **Tuzatish:** `_is_answer_correct` funksiyasida `correct = q.get("correct_answer") or q.get("correct")` qoidasi joriy etildi.
- **Baza sinxronizatsiyasi:** `scratch/fix_all_test_questions.py` orqali bazadagi barcha A1–C2 testlarining savollarida ikkala kalit ham sinxronlandi va o'tish bali standart `70.0%` ga to'g'rilandi.

---

### 4. 📱 O'quvchi WebApp API Kengaytmasi (`backend/api/routes/student.py`)
- **`GET /api/student/schedule`:** O'quvchining barcha faol guruhlari, guruh nomi, dars vaqtlari, xona raqami, zoom havolasi va o'qituvchi ismini qaytaruvchi yangi endpoint qo'shildi (`aliased(User)` xavfsiz bog'lanishi bilan).
- **`GET /api/student/homework`:** O'quvchi a'zo bo'lgan guruhlarning eng so'nggi faol uy vazifalari, tavsifi, topshirish muddati va fayllarini qaytaruvchi endpoint ishga tushirildi.

---

### 5. 🛡 Testlashda Shaxsiy Akkauntdan Xoli Bo'lish (`test_suite.py`)
- **Shaxsiy akkaunt himoyasi:** `test_suite.py` test topshirishda shaxsiy admin Telegram ID si o'rniga maxsus fake student akkaunti (`7100000010`) ga o'tkazildi.
- **`send_fake_account_requests.py`:** 5 ta o'qituvchi va 15+ ta o'quvchi nomidan real vaqtda FastAPI ga so'rovlar (Test topshirish, progressni ko'rish, o'qituvchi kabineti) yuboruvchi test simulyatori yaratildi.

---

### 6. 🌟 To'liq Ekotizim Sikli Simulyatori (`run_full_lifecycle_flow.py`)
- **7 bosqichli to'liq avtomatlashtirish:**
  1. Admin yangi IELTS va General English guruhlarini ochadi.
  2. Yangi o'quvchilar daraja testini topshirib, Free Darsga ariza jo'natadi.
  3. O'qituvchilar Free Darsni qabul qilib, sinov darsini o'tishadi.
  4. O'quvchilar to'lov qiladi va admin to'lovni tasdiqlab, guruhga a'zo qiladi.
  5. O'qituvchilar yangi guruhga uy vazifasi biriktiradi.
  6. O'qituvchi dars davomatini belgilaydi.
  7. O'quvchilar yangilangan dars jadvali va uy vazifalarini ko'radi.

---

### 7. 👑 Master Ekotizim Testi (15/15 Barcha Funksiyalar Sinovi — `master_ecosystem_test.py`)
- **To'liq qamrovli master sinov:**
  1. 📝 Yangi test yaratish (`POST /api/teacher/save-test`)
  2. 👨‍🏫 Yangi o'qituvchi tayinlash (`POST /api/admin/teachers`)
  3. 🛡 Yangi admin tayinlash (`POST /api/admin/admins`)
  4. 👥 Yangi guruh ochish (`POST /api/admin/groups`)
  5. 🎯 Free Dars arizasi yuborish va o'qituvchi dars o'tishi (`FreeTrialRequest`)
  6. 💳 To'lovlar: Naqd to'lovni tasdiqlash va Payme Online Webhook to'lovi (`PerformTransaction`)
  7. 💬 Bot orqali Support Chat (savol berish, adminga borishi, javob berilib yopilishi)
  8. 🎁 Referal tizimi: Do'stini taklif qilish, +5% kümülyativ chegirma va Ambassador badge
  9. 📋 Yangi guruhga uy vazifasi yuklash va o'quvchi tomonidan qabul qilish
  10. 🚫 O'quvchini guruhdan chetlatish (`EnrollmentStatusEnum.dropped`)
  11. 🔄 O'quvchi guruhini almashtirish (`GroupChangeRequest` tasdiqlanishi)
  12. 📊 O'quvchi progressi (davomat %, test ballari, nishonlar)
  13. ✍️ Oddiy daraja testini topshirish va baholash
  14. 📢 Reklama / Ommaviy xabarnoma tarqatish (`POST /api/admin/broadcast`)
  15. 🎓 ReportLab orqali rasmiy PDF sertifikat yaratish (`generate_certificate_pdf`)

---

### 📌 Yodda saqlangan (Kelgusi yaxshilanishlar uchun reja):
- **Katta guruhlar uchun tezkor davomat (Quick Pick):** 20-30 kishilik guruhlarda kechikib kelgan o'quvchini boshidan qayta bosmasdan, to'g'ridan-to'g'ri ro'yxatdan tanlab 1 ta bosishda statusini o'zgartirish mexanizmi.

---

## 🚀 [2026-09-01] — Katta Yangilanish (v2.6.5)

### 1. 🛡 Ro'yxatdan O'tish & Kontakt Xavfsizligi
- **Qat'iy raqam tekshiruvi:** Ro'yxatdan o'tishda va sozlamalarda faqat foydalanuvchining o'z Telegram akkauntiga tegishli raqami (`message.contact.user_id == message.from_user.id`) qabul qilinadi.
- **Forward bloklash:** Boshqa shaxslar yoki kanallardan forward qilingan kontaktlar butunlay taqiqlandi.
- **Qo'lda raqam kiritishni cheklash:** Soxta raqamlarning oldini olish uchun faqat rasmiy `[📱 Raqamni yuborish]` tugmasi orqali qabul qilinadi.
- **Avtomatik Admin roli:** `.env` dagi `ADMINS=1435473812` foydalanuvchisi ro'yxatdan o'tishi bilan unga avtomatik tarzda `RoleEnum.admin` beriladi.
- **Soxta raqamlar tozalandi:** Bazadagi statik `+998901112233` fake raqami olib tashlandi (`phone=None`).

---

### 2. 🎯 Sinov Darslari Davomati (Free Trial UX)
- **Maxsus Davomat Menusi:** «👥 Davomat olish» bo'limida yangi **«🎯 Sinov darslari davomati»** ro'yxati yaratildi. O'qituvchi/Admin kutilayotgan barcha sinov darslari o'quvchilarini ko'rib, bitta bosishda `[🟢 Darsga Keldi]` yoki `[🔴 Kelmadi]` belgilashi mumkin.
- **Avtomatik Eslatma (Scheduler):** Agar sinov darsi davomati 2 soatdan ortiq vaqt belgilanmay qolsa, bot o'qituvchiga to'g'ridan-to'g'ri eslatma va tugmalar yuboradi.
- **To'lov tugmasi tuzatildi:** O'quvchi sinov darsini baholagach chiqqan `[💳 Rasmiy guruhga to'lov qilish]` (`start_payment_flow`) callback handler ulandi va guruh to'lovi oynasi darhol ochiladigan qilindi.

---

### 3. 📢 Broadcast (Ommaviy Xabarnoma) Takomillashuvi
- **`@postbot` Inline Tugmalarini Saqlash:** `@postbot` yoki boshqa inline botlar orqali yaratilgan postlar barcha inline tugmalari bilan to'liq va buzilmasdan tarqatiladi.
- **Forward Xabarlar:** Admin kanallardagi postlarni botga forward qilganda:
  1. `⏩ Asl nusxada Forward qilish` (kanal nomi va havolasi bilan)
  2. `📋 Bot nomidan Copy qilish` (toza post sifatida)
  variantlari qo'shildi.

---

### 4. 🛠 AI Test Builder & Test Boshqaruvi
- **Eng so'nggi testlar ustuvorligi:** `GET /api/tests/by-level/{level}` so'rovi `.order_by(Test.created_at.desc())` qoidasi bilan yangilandi. Yangi yuklangan yoki tahrirlangan testlar darhol o'quvchi sahifasida chiqadi.
- **Mavjud Testlar Ro'yxati:** `TestBuilder.jsx` sahifasida barcha IELTS, CEFR va General English testlarini ko'rish bo'limi qo'shildi.
- **Savollarni Tahrirlash (Edit):** Istalgan testni tanlab, uning barcha savollari, variantlari va to'g'ri javoblarini tahrirlash, yangi savol qo'shish yoki o'chirish imkoniyati yaratildi (`PUT /api/teacher/tests/{id}`).
- **Animatsiyali Bildirishnoma:** Test muvaffaqiyatli saqlanganda yoki yangilanganda yashil yaltiroq banner orqali *"🎉 Test muvaffaqiyatli saqlandi va faollashtirildi, o'quvchilar ishlashiga tayyor!"* xabari chiqadi.

---

### 5. 🎨 WebApp Dark Glassmorphism Luxury Dizayni
- **AdminDashboard:** Qorong'u kiber-estetika (Dark glassmorphism), yaltiroq gradient kartalar, jonli KPI ko'rsatkichlar va blur backdrop effektlari bilan yangilandi.
- **TestBuilder:** Professional AI tahlil paneli va zamonaviy savol tahrirlagichi yaratildi.
- **Tezkor build:** Vite React frontend 600ms ichida 0 xatolik bilan yig'ilishi ta'minlandi.

---

### 6. 👨‍🏫 O'qituvchilarni Qo'shish va Boshqarish Tizimi
- **Web App Admin Dashboard:** Yangi **«👨‍🏫 O'qituvchilar»** bo'limi yaratildi. Admin o'qituvchilar ro'yxatini, biriktirilgan guruhlarini ko'rishi, `[➕ Yangi O'qituvchi Qo'shish]` modali orqali yangi o'qituvchi tayinlashi yoki `[🗑 O'chirish]` orqali vazifasidan ozod qilishi mumkin.
- **Backend API:** `GET /api/admin/teachers`, `POST /api/admin/teachers`, `DELETE /api/admin/teachers/{teacher_id}` endpointlari joriy etildi.
- **Telegram Bot Buyruqlari:** 
  - `/add_teacher [TELEGRAM_ID] [Ism Familiya]` — Istalgan foydalanuvchiga bir zumda O'qituvchi (Teacher) rolini beradi va unga bildirishnoma yuboradi.
  - `/teachers` — Mavjud barcha o'qituvchilar ro'yxatini ko'rish.
  - `/remove_teacher [TELEGRAM_ID]` — O'qituvchini o'quvchi roliga tushirish.
- **Guruhlarga biriktirish:** Yangi guruh ochish yoki tahrirlashda o'qituvchilar ro'yxati avtomatik shakllanadi.

---

### 7. ⏰ Uy Vazifasi Eslatmalari Vaqtini Qat'iy Dars Jadvaliga Bog'lash
- **Aniq Vaqt Hisob-kitobi:** Oldin barcha guruhlar bo'yicha har 15 daqiqada tekshirib darhol ogohlantirish yuborayotgan edi. Endi `scheduler.py`:
  1. Faqat **bugun dars kuni bo'lgan** (Monday, Tuesday va h.k.) guruhlarni tekshiradi.
  2. Dars boshlanish vaqti (`16:00`, `18:00` va h.k.) + dars davomiyligini hisoblab, **dars tugaganidan roppa-rosa 3 soat o'tganidagina** tekshiradi.
  3. Yangi ochilgan guruhlar yoki darsi hali bo'lmagan guruhlarga behuda xabar bormaydi.
  4. Bir kunda har bir dars uchun faqat 1 marta eslatma va eskalatsiya yuboriladi (spam oldi olindi).

---

### 8. 🗓 Guruh Ochishda Dars Kunlarini Tanlash (Schedule Days Selector)
- **Interaktiv Hafta Kunlari:** Guruh ochish yoki tahrirlash modalida haftaning istalgan kunlarini erkin tanlash imkoniyati yaratildi (`Dush`, `Sesh`, `Chor`, `Pay`, `Jum`, `Shan`, `Yak`).
- **Tezkor Andozalar (Presets):** 
  - `✨ Toq kunlar (Dush-Chor-Jum)`
  - `✨ Juft kunlar (Sesh-Pay-Shan)`
  - `✨ Har kuni (Dush-Shan)`
  - `✨ Dam olish kunlari (Shan-Yak)`
- **Avtomatik Sinxronizatsiya:** Guruh tahrirlanganda mavjud dars kunlari to'g'ri o'qib olinadi va tanlangan holda ko'rsatiladi.

---

### 9. 🔍 Test Natijalarida Xatolar Tahlili (Detailed Test Review)
- **Savollar bo'yicha batafsil tahlil:** Test topshirilgandan so'ng ekranda barcha savollarning to'liq tahlili (`review`) chiqadi.
- **Filtrlash imkoniyati:** `[Barchasi]` | `[✅ To'g'ri]` | `[❌ Xatolar]` filter tugmalari orqali xatolarni ajratib ko'rish.
- **Variantlar taqqoslash:** 
  - To'g'ri ishlangan savollarda: Yashil yaltiroq badge bilan `✓ To'g'ri javob`.
  - Xato ishlangan savollarda: Qizil rangda `✗ Sizning javobingiz` va yonida yashil rangda `✓ To'g'ri javob` ko'rsatiladi.
- **O'quvchi uchun mustahkam o'rganish:** O'quvchi o'z xatolarini darhol ko'rib, qayerda adashganini tushunadi.

---

### 10. 🔗 Guruh Havolalari & Profil Integratsiyasi
- **Guruh Telegram Havolasi:** Guruh ochish/tahrirlash modalida `🔗 Guruh Telegram Chat Havolasi` (masalan, `https://t.me/+...`) va `🎥 Zoom Havolasi` kiritish maydonlari qo'shildi.
- **O'quvchi Profilida Chiqishi:** O'quvchi kursga rasman a'zo bo'lgach, «👤 Profilim» bo'limida o'z guruhining Telegram chati havolasini ko'radi va `[👥 Guruh Telegram Chati]` tugmasi orqali to'g'ridan-to'g'ri qo'shila oladi.

---

### 11. 🔄 Xabarlarni Toza Tahrirlash (Clean Message Updates)
- Sinov darsidan so'ng baholash berilganda `[💳 Rasmiy guruhga to'lov qilish]` bosilganda, eski fikr-mulohaza xabari to'g'ridan-to'g'ri to'lov oynasiga almashtiriladi (dublikat xabarlar to'planib qolishi bartaraf etildi).

---

### 12. 🐛 Ro'yxatdan O'tishda RoleEnum Xatosi Tuzatildi
- `app/handlers/users/start.py` faylida `RoleEnum` import qilinmagani sababli kelib chiqqan `NameError` to'liq bartaraf etildi. Referal orqali yoki to'g'ridan-to'g'ri kirgan barcha yangi o'quvchilar xatosiz ro'yxatdan o'tadi.

---

### 13. 📱 Test Variantlari va Pastki Qoplash Muammosi Tuzatildi
- **Barcha 4 ta Variant To'liq:** Bazadagi test savollarining barchasi 4 ta to'liq variantga (`A, B, C, D`) ega bo'lishi ta'minlandi.
- **Pastki Tugma Qoplab Qolmasligi:** Ekran pastidagi suzuvchi `[🚀 Testni yakunlash]` tugmasi oxirgi savolning variantlarini yopib qo'ymasligi uchun pastki bo'shliq (`h-28 spacer` va `pb-44`) kengaytirildi.
- **Toza Matn:** Variant matnlaridagi takroriy `A)` / `B)` harflari tozalanib, chiroyli dizayndagi harf nishoni (`[A]`) bilan ko'rsatildi.

---

### 14. ⚙️ Markaz Kontakt Sozlamalari Boshqaruvi (Center Settings)
- **To'liq Dinamik Bazadan:** Botdagi «📞 Bog'lanish» bo'limidagi barcha ma'lumotlar (telefon, admin username, manzil) to'g'ridan-to'g'ri `center_settings` ma'lumotlar bazasidan olinadi.
- **Admin Panelda Sozlash:** WebApp Admin Dashboardga **«⚙️ Sozlamalar»** bo'limi qo'shildi. Admin markaz telefonini, Telegram usernameni va ko'p tilli manzillarni (UZ/RU/EN) tahrirlab saqlashi bilan botda bir zumda avtomatik yangilanadi.

---

### 15. 💰 Refund Tasdiqlanganda O'quvchini Guruhdan Avtomatik Chiqarish
- **Avtomatik Chiqarish (Unenroll):** Bot orqali yoki WebApp Admin Panel orqali Refund tasdiqlanganda:
  1. O'quvchining a'zolik holati `is_active=False`, `status="dropped"` qilinadi.
  2. To'lov holati `PaymentStatusEnum.refunded` ga o'tkaziladi.
  3. `refunds` jadvaliga to'liq audit yozuvi kiritiladi.
  4. O'quvchiga qaytarilgan summa va guruh a'zoligidan chiqarilgani haqida rasmiy bildirishnoma yuboriladi.
- **Admin Dashboard Harakati:** To'lovlar ro'yxatida tasdiqlangan to'lovlar yonida **`[💰 Refund]`** tugmasi qo'shildi (bir bosishda refund va guruhdan chiqarish).

---

### 16. 🔒 Support Muloqot Yopilishi va Timeout Muammosi Bartaraf Etildi
- **Yagona Faol Chat (Single Session):** O'quvchi bir nechta savol yozsa yoki javob qaytarsa, har safar yangi muloqot ochilmasdan, mavjud ochiq sessiya yangilanadigan bo'ldi.
- **To'liq Yopilish (Cascade Resolution):** Admin yoki o'quvchi «🔒 Suhbatni yakunlash» tugmasini bosganda, shu o'quvchiga tegishli barcha ochiq muloqotlar to'liq `closed` (`reason=resolved`) holatiga o'tkaziladi.
- **Scheduler Himoyasi:** 15 daqiqalik fon tekshiruvi (`check_support_chat_timeouts`) muloqot yopilganidan so'ng qayta asossiz timeout xabari yubormasligi ta'minlandi.

---

### 17. 📖 Uyga Vazifa Qo'shilganda O'quvchilarga Avtomatik Xabarnoma Yuborish
- **Matnli Qulay Bildirishnoma:** O'qituvchi yoki Admin guruhga yangi uy vazifasi qo'shganda, o'quvchilarga og'ir fayllar to'g'ridan-to'g'ri tashlanmasdan, toza va chiroyli matnli xabarnoma boradi:
  * «📖 **UYGA VAZIFA YUKLANDI!** Guruh, Mavzu, Tavsif, Topshirish muddati».
  * Xabar ostidagi **`[📋 Uyga vazifani tekshirish]`** tugmasi orqali o'quvchi to'g'ridan-to'g'ri vazifa bo'limiga kirib, topshiriq tafsilotlari va biriktirilgan fayllarni o'z xohishiga ko'ra yuklab olishi mumkin.

---

### 18. 💳 To'lov Tasdiqlashda Xatolik Bartaraf Etildi & Guruh Havolasi
- **SQLAlchemy Detached Xatosi Tuzatildi:** Online to'lov (karta / Payme / Click) tasdiqlanganda va naqd to'lov tasdiqlanganda `session.commit()` dan keyin obyekt xususiyatlariga murojaat qilish tufayli terminalda paydo bo'lishi mumkin bo'lgan barcha xatoliklar to'liq bartaraf etildi.
- **To'lovdan So'ng Darhol Guruh Chati:** To'lov muvaffaqiyatli yakunlangach, ekranga chiqadigan tabrik xabarining o'zidayoq **`[👥 Guruh Telegram Chati]`** tugmasi qo'shildi, o'quvchi to'lov qilishi bilan guruhiga ulanadi.

---

### 19. 📝 AI va Qo'lda Test Yaratishda Ko'p Turdagi Savollar va PDF Layout Tahlili
- **Passage (O'qish matni) ni Barcha Tegishli Savollarga Biriktirish:** Agar matn (Reading passage) 1- va 2-savollarga (yoki 1-5 gacha) tegishli bo'lsa, sun'iy intellekt ushbu matnni har ikkala savolning boshiga birdek joylaydi. O'quvchi har bir savolni ishlayotganda matnni doimiy ko'rib turadi.
- **Qog'ozdagi Javob Chiziqlarini (_____) Avtomatik Tozalash:** Qog'ozdagi testlarda ochiq savoldan keyin talaba qalamda yozishi uchun qo'yilgan chiziqlar (`________________`, `----------------`) savol matnidan to'liq tozalanadi va savol toza "short_answer" formatiga o'tkaziladi.
- **To'liq Shart va Matnni Saqlash:** Agar savol biror topshiriq ko'rsatmasiga (Instructions: masalan, *«Choose NO MORE THAN TWO WORDS»*, *«Read the passage and answer questions 1-5»*) tegishli bo'lsa, ushbu shart to'liq saqlanadi.
- **Cheksiz Matn Uzunligi & 8K Tokens:** AI tahlili uchun matn limiti 100,000 belgiga (butun kitob/test sahifalari hajmiga) va javob chiqarish buferi 8,192 tokenga oshirildi (hech bir savol yoki sahifa uzilib qolmaydi).
- **Google Gemini AI Integratsiyasi:** `.env` orqali Google Gemini AI modeli to'liq ulandi va muvaffaqiyatli sinovdan o'tkazildi (PDF matnlaridan 100% aniqlik bilan savollarni tahlil qiladi).
- **PDF Layout & Matn O'qish Inqilobi:** PDF'dagi ko'p ustunli (2-column layout), jadvalli va qiya matnlar `extraction_mode="layout"` orqali qatorlari buzilmasdan, chiziqcha bilan bo'lingan so'zlari (`exam-\nple` -> `example`) birlashtirilib toza o'qiladigan bo'ldi.
- **Answer Key Avtomatik Ajratish:** Matn oxiridagi javoblar kaliti (`Answers: 1. A, 2. True, 3. 0`) alohida xotiraga olinib, asosiy savollar matnidan avtomatik qirqib tozalanadi.
- **AI Tahlilida Choice Yo'q Savollar Muammosi Bartaraf Etildi:** PDF matnidan test generatsiya qilinganda, faqat 4 variantli savollar emas, balki **True/False**, **Bo'sh joyni to'ldirish (Fill in the blanks: `____`)** va **Ochiq/Qisqa yozma javobli (Short answer)** barcha savollar to'liq ajratib olinadi.
- **Qo'lda Savol Yaratish Kengaytirildi:** O'qituvchi Test Builderdan savol qo'shganda yoki tahrirlaganda bir zumda 4 xil savol turini tanlashi mumkin:
  * `🔘 Variantli (MCQ)` — variantlar qo'shish/o'chirish va to'g'ri variantni belgilash.
  * `⚖️ True / False` — 2 ta katta interaktiv tugma orqali to'g'ri javobni tanlash.
  * `✍️ Bo'sh joyni to'ldirish (Fill in Blank)` — to'g'ri so'z/iboralar kiritish.
  * `📝 Ochiq / Qisqa javob (Short Answer)` — bir nechta to'g'ri sinonim javoblarni (`/` orqali) kiritish.
- **Aqlli Test Baholash Tizimi:** O'quvchi test ishlaganda har bir savol turiga mos interfeys (variantlar, True/False tugmalari yoki matn kiritish maydoni) chiqadi. Baholashda katta-kichik harflar va sinonim javoblar inobatga olinadi.

---

### 20. 🧹 Toza Baza (Clean Slate Testing)
- `scratch/wipe_clean_database.py` skripti yaratildi: bazani to'liq 0 holatga keltirib, faqat Bosh Admin (`1435473812`) uchun toza ro'yxatdan o'tish muhitini yaratadi.

---

### 21. 🛡 Qaytarish (Refund) va Guruh Almashtirishda Tugmalar Bosilishi Xatosi Tuzatildi
- **Navigatsiya va Menyular Himoyasi:** Refund yoki Guruh almashtirish sababi so'ralganda, o'quvchi/admin `👑 Admin Panel` yoki boshqa menyu tugmalarini (`👤 Profilim`, `📚 Kurslar`, `/admin`, `/start`) bosganda, ushbu tugma nomi sabab sifatida qabul qilinmaydi. Buning o'rniga so'rov bekor qilinadi va foydalanuvchi tanlagan bo'limiga to'g'ri yo'naltiriladi.
- **Bekor Qilish Tugmasi:** Sabab so'raladigan xabarga to'g'ridan-to'g'ri `[❌ Bekor qilish]` inline tugmasi qo'shildi.
- **Sababni Validatsiya Qilish:** Juda qisqa (5 tadan kam belgi) yoki tasodifiy kiritilgan so'zlar qabul qilinmasdan, to'liqroq tushuntirish kiritish so'raladi.

---

### 22. 👥 Xodimlar: O'qituvchilar va Adminlarni Bir Qatorda Boshqarish (Web App & Bot)
- **Web App Admin Dashboardda Yangi Qator & Vkladka:** `👨‍🏫 O'qituvchilar` vkladkasi bilan bir qatorda **`👑 Adminlar`** vkladkasi qo'shildi.
- **Yangi Admin Qo'shish & O'chirish (Modal & API):** Dashboardda `➕ Yangi Admin Qo'shish` tugmasi va modali yaratildi (Telegram ID, Ism, Telefon, Username kiritib darhol admin qilish mumkin). Istalgan adminni `🗑 O'chirish` tugmasi orqali lavozimidan ozod qilish mumkin.
- **Telegram Bot Admin Menyu Qatori:** Botning `👑 Admin Panel` reply klaviaturasiga alohida `👨‍🏫 O'qituvchilar` va `👑 Adminlar` tugmalari qatori kiritildi.
- **Yangilangan Boshqaruv Markazi Xush Kelibsiz Xabari:** Telegram botdagi `/admin` xabari va WebApp'dagi asosiy banner yangilanib, tizimga kiritilgan barcha so'nggi yangiliklar (Adminlar va Ustozlar boshqaruvi, Gemini AI PDF testlari, Kassa & Refund, Telegram chat havolalari) to'liq aks ettirildi.

---

### 23. 👨‍🏫 Maxsus O'qituvchi Kabineti va Qat'iy Rol Ajratish (Web App & Bot)
- **O'qituvchi Sahifasida Sozlamalar va Switcherlar Yo'qotildi:** O'qituvchi kabineti (`TeacherDashboard.jsx`) faqat o'qituvchining shaxsiy darslariga, guruhlariga va o'quvchilariga yo'naltirildi. Unda hech qanday umumiy markaz sozlamalari (`⚙️ Sozlamalar`) va rejim almashtirish tugmalari ko'rsatilmaydi.
- **Telegram Botda Alohida `👨‍🏫 O'qituvchi Kabineti` Tugmasi:** Bot menyusiga to'g'ridan-to'g'ri o'qituvchi sahifasini ochuvchi `👨‍🏫 O'qituvchi Kabineti` WebApp tugmasi qo'shildi. O'qituvchilar menyusidan moliyaviy va ma'muriy (kassa, refund, adminlar) tugmalar butunlay olib tashlandi.
- **Avtomatik Rol Himoyasi (App.jsx):** O'qituvchi tizimga kirganda, unga majburiy tarzda faqat o'qituvchi kabineti ochiladi va admin sozlamalari bloklanadi.

---

### 24. 🎯 3 Bosqichli Qat'iy Rol Matritsasi (Faqat Ustoz, Faqat Admin, Ham Admin / Ham Ustoz)
Tizim 3 ta aniq rol holatiga to'liq moslashtirildi:
1. **Faqat O'qituvchi bo'lsa:**
   - Web App'da: Faqat **Ustoz Kabineti** (`TeacherDashboard`) ochiladi. Unda hech qanday sozlamalar, kassa, tushum yoki admin vkladkalari bo'lmaydi.
   - Telegram Botda: Faqat `[ 👨‍🏫 O'qituvchi Kabineti ]`, `[ 🛠 Test Builder ]`, davomat, uy vazifasi va sertifikat tugmalari beriladi.
2. **Faqat Administrator bo'lsa (Dars o'tmaydigan admin):**
   - Web App'da: Faqat **Admin Dashboard** (`AdminDashboard`) ochiladi. Unda ustoz kabinetiga o'tish tugmasi va darslar vkladkasi ko'rsatilmaydi.
   - Telegram Botda: Faqat `[ 📊 Admin Dashboard ]`, kassa, refund, o'qituvchilar va adminlar tugmalari beriladi.
3. **Ham Administrator, Ham O'qituvchi bo'lsa (Masalan, markaz asoschisi / Anvar Sobirov):**
   - Web App'da: Admin Dashboard ichida **`👨‍🏫 Mening Darslarim`** vkladkasi va tepada **`[ 👨‍🏫 Ustoz Kabineti ]`** tugmasi orqali ikkala sahifaga ham to'liq, qulay va tezkor kirish imkoniyati beriladi.
   - Telegram Botda: `[ 📊 Admin Dashboard ]` va `[ 👨‍🏫 O'qituvchi Kabineti ]` ikkala tugma ham birgalikda taqdim etiladi.

---

### 25. 🧪 Tizimni To'liq Testlash va Test O'tkazish Xatoligini Bartaraf Etish
- **Import xatoligi tuzatildi (`import re`):** `backend/api/routes/tests.py` da o'quvchi test javobini topshirganda harf prefikslarini (`A) Option`) tozalovchi `re.sub` funksiyasi uchun `import re` ulanmaganligi aniqlanib, tuzatildi.
- **Barcha CEFR Darajalari Testlari (A1 dan C2 gacha):** Barcha darajalar (A1, A2, B1, B2, C1, C2) uchun rasmiy sinov placement testlari bazaga kiritildi va tekshirildi.
- **100% Test Natijasi:** Asosiy test to'plamlari (`test_suite.py`, `master_verification.py`, `test_student_full_journey.py`) 100% muvaffaqiyat bilan yakunlandi (11/11 ta test o'tdi).
- **Haqiqiy Test Foydalanuvchilari:** Markaz bo'yicha 10 nafar faol o'quvchi, 2 ta faol kurs va guruhlar (`GA | Odd` va `IELTS-1 | Even`) real to'lovlar bilan sinovdan o'tkazildi.

---

## 📦 [2026-08-30] — Asosiy Funksiyalar (v2.6.0)
- Click & Payme to'liq webhook integratsiyasi (Prepare, Complete, JSON-RPC).
- Excel (.CSV) formatda to'lovlar va talabalar hisobotlarini yuklab olish.
- 24 soatlik test retake cooldown va 1 daraja past test tavsiya qilish mexanizmi.
- Gamifikatsiya (Badges: Starter, Regular, Master, Homework Hero, Ambassador).
- Darsdan keyin 3 soatlik uy vazifasi eslatmasi va adminlarga eskalatsiya tizimi.
- Jonli support chat 15 daqiqalik avtomatik timeout tizimi.
- Pulni qaytarish (Refund) avtomatlashtirilgan formulasi va guruh almashtirish so'rovlari.
