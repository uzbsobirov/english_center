# 📚 Ingliz Tili O'quv Markazi — Telegram Bot + Web App
## Texnik Topshiriq (TZ) — v2.6

> **v2.6 o'zgarishlari:** Yangi bo'lim qo'shildi — **7.5.1 PDF'dan AI orqali test yaratish**. O'qituvchi endi savollarni qo'lda kiritish o'rniga PDF yuklab, AI yordamida avtomatik test generatsiya qila oladi (self-check bilan, shubhali savollarga ⚠️ warning).

---

## 1. Loyiha Maqsadi

IELTS va CEFR yo'nalishlarida ingliz tili o'qitiladigan markaz uchun to'liq raqamli platforma yaratish. Platforma ikki qismdan iborat:

- **Telegram Bot** — o'quvchilar, o'qituvchilar va adminlar kundalik operatsiyalar uchun
- **Web App (Telegram Mini App)** — qulay interfeys: admin panel, o'qituvchi panel, test ishlash, progress va jadval

> ℹ️ O'quvchi kursga yozilishdan oldin albatta 1 ta **FREE dars**da qatnashadi. Faqat shundan keyin to'lov va rasmiy yozilish amalga oshadi.

---

## 2. Texnologiyalar

| Komponent | Texnologiya | Izoh |
|-----------|-------------|------|
| Bot | Python + aiogram 3 | Asosiy bot logikasi |
| Web App | React + Vite + TailwindCSS | Telegram Mini App |
| Backend API | FastAPI (Python) | Bot va Web App uchun umumiy API |
| Ma'lumotlar bazasi | PostgreSQL | Asosiy ma'lumotlar |
| Cache / Sessiya | Redis | Tez so'rovlar |
| ORM | SQLAlchemy + Alembic | Migratsiyalar bilan |
| Hosting | VPS / Railway | SSL sertifikat bilan |
| To'lov | Payme, Click, Uzum, Naqd | 4 ta usul |
| Fayllar | Telegram File Storage | Rasm, audio, PDF |
| Scheduler | APScheduler | Eslatmalar va cronlar |

---

## 3. Tillar

Bot to'liq **3 tilda** ishlaydi. Foydalanuvchi istalgan vaqtda tilni o'zgartira oladi:
- 🇺🇿 O'zbek tili — asosiy til
- 🇷🇺 Rus tili — to'liq tarjima
- 🇬🇧 Ingliz tili — to'liq tarjima

---

## 4. Web App — Umumiy Arxitektura

Web App Telegram Mini App sifatida ishlaydi. Har bir rol o'z paneliga kiradi:

| Rol | Web App Sahifalari |
|-----|--------------------|
| 🔴 Admin | Dashboard, Kurslar, Guruhlar, O'quvchilar, To'lovlar, Broadcast, Hisobot, Jadval, O'qituvchilar |
| 🟡 O'qituvchi | Guruhim, Davomat, To'lovlar, Uy vazifasi, Test yaratish, O'quvchi profili |
| 🟢 O'quvchi | Testlar, Progress, Jadval, Uy vazifasi, Profil |

> ℹ️ Web App Telegram user ID orqali avtomatik autentifikatsiya qiladi. Parol kerak emas.

---

## 5. Foydalanuvchi Rollari va Huquqlari

Tizimda 4 ta rol mavjud:

| Funksiya | Super Admin | Manager | O'qituvchi | O'quvchi |
|----------|-------------|---------|------------|---------|
| Kurs qo'shish / tahrirlash | ✅ | ✅ | ❌ | ❌ |
| Guruh yaratish / tahrirlash | ✅ | ✅ | ❌ | ❌ |
| O'quvchini guruhga qo'shish | ✅ | ✅ | ❌ | ❌ |
| O'quvchini guruhdan chiqarish | ✅ | ✅ | Tavsiya beradi | ❌ |
| Guruh o'zgartirish (o'quvchi uchun) | ✅ | ✅ | Tasdiqlaydi | So'rov yuboradi |
| To'lovni tasdiqlash (naqd) | ✅ | ✅ | ✅ faqat o'z guruhi | ❌ |
| To'lovni ko'rish | ✅ barchasi | ✅ barchasi | ✅ faqat o'z guruhi | ✅ faqat o'ziniki |
| Broadcast yuborish | ✅ | ✅ | ❌ | ❌ |
| Davomat qo'yish | ✅ | ✅ | ✅ faqat o'z guruhi | ❌ |
| Uy vazifasi qo'shish | ✅ | ✅ | ✅ faqat o'z guruhi | ❌ |
| Test yaratish | ✅ | ✅ | ✅ faqat o'z guruhi | ❌ |
| Test ishlash | ❌ | ❌ | ❌ | ✅ |
| O'z statusini ko'rish | — | — | — | ✅ |
| Moliya hisoboti | ✅ | ✅ ko'rish | ❌ | ❌ |
| O'qituvchi qo'shish | ✅ | ❌ | ❌ | ❌ |

---

## 6. O'quvchi Flow

### 6.1 Botga Birinchi Kirish
1. `/start` — bot ochiladi
2. Til tanlash: 🇺🇿 O'zbek / 🇷🇺 Rus / 🇬🇧 English
3. Ism va telefon raqam so'raladi
4. Asosiy menyu ko'rsatiladi

### 6.1.1 To'g'ridan-to'g'ri Free Darsga Yozilish (daraja tanlab)

Main menyuga **«📝 Free darsga yozilish»** tugmasi qo'shiladi. Bu yerda test butunlay yo'qolmaydi — faqat oqim boshqacha ishlaydi:

1. O'quvchi tugmani bosadi
2. Sertifikat turi (IELTS/CEFR) tanlanadi
3. O'quvchi **o'zi darajasini tanlaydi** (masalan B1)
4. Tizim shu darajaga mos testni beradi
5. Agar o'quvchi **o'tish balidan** (`tests.passing_score`, DB'dan olinadi) yuqori ball olsa → shu daraja guruhiga yozilish jarayoni boshlanadi (7.1.1 dagi «birinchi bosgan g'olib» mexanizmi bilan o'qituvchi tayinlanadi)
6. Agar o'ta olmasa → tizim avtomatik **bir daraja pastroq** test taklif qiladi (masalan B1 dan o'tolmasa — A2 testi)
7. Shu tartibda pasayib, o'quvchi o'ta oladigan darajasi topilguncha davom etadi

> ℹ️ DB: `tests` jadvaliga `passing_score DECIMAL(5,2)` (yoki `passing_percentage`) maydoni qo'shiladi — har bir test/daraja uchun alohida o'tish bali belgilanadi.

### 6.2 Daraja Testi → Free Dars → Yozilish
1. O'quvchi **🎯 Testlar** bo'limiga kiradi
2. Sertifikat turini tanlaydi: IELTS yoki CEFR
3. Darajani tanlaydi yoki «Bilmayman, aniqlang» deydi
4. Testni Web App da ishlaydi (MCQ, fill-in, audio, translation)
5. Natija chiqadi — daraja aniqlanadi (masalan B1)
6. Tizim B1 guruhlarining barcha o'qituvchilariga xabar yuboradi
7. O'qituvchi «Free darsga taklif qilish» tugmasini bosadi — **birinchi bosgan o'qituvchi tayinlanadi** (7.1.1 ga qarang), qolganlarga "band qilindi" ko'rsatiladi
8. O'quvchiga xabar: *«Siz B1 free darsiga [sana], soat [vaqt], [manzil]da kelishingiz mumkin»*
9. O'quvchi free darsga boradi — dars kuni o'qituvchi botda **«Keldi ✅ / Kelmadi ❌»** deb belgilaydi (`free_trial_requests.status` shu yerda `attended`/`declined`ga o'zgaradi)
10. Darsdan so'ng o'quvchi botda **rate qoldiradi** (1-5 yulduz + izoh)
11. O'quvchi «Davom etaman» yoki «Yo'q, rahmat» tugmasini bosadi
12. Davom etmoqchi bo'lsa — tizim guruhda joy borligini tekshiradi (6.2.1 ga qarang), so'ng o'qituvchi to'lov eslatmasini yuboradi
13. O'quvchi to'lovni amalga oshiradi (Payme / Click / Uzum / Naqd)
14. O'qituvchi naqd to'lovni bot orqali tasdiqlaydi → o'quvchiga xabar keladi
15. O'quvchi rasmiy guruhga qo'shiladi ✅

### 6.2.1 Guruh to'lgan holat

- O'quvchi guruhga qo'shilishidan oldin tizim `groups.max_students` bilan joriy o'quvchilar sonini solishtiradi.
- Agar guruh **to'lgan** bo'lsa, tizim quyidagi tartibda harakat qiladi (waiting list — oxirgi variant):
  1. Bir xil kurs/daraja bo'yicha **joyi bor boshqa guruh** qidiriladi va o'quvchiga tavsiya qilinadi (asosiy yechim)
  2. Agar shu daraja/kursda mutlaqo bo'sh guruh topilmasa — **faqat shunda** o'quvchi kutish ro'yxatiga (`waiting_list`) qo'shiladi
- `max_students` admin panelda istalgan vaqtda tahrirlanadi.

### 6.3 Kundalik Foydalanish
- 📋 Uy vazifasini ko'rish (keyingi darsgacha muddat)
- 📅 Dars jadvalini ko'rish
- 🎯 Istalgan vaqtda test ishlash (Web App)
- 📁 Dars materiallarini yuklab olish
- 📊 O'z progressini ko'rish (Web App)
- 🏆 Guruh reytingini ko'rish
- 🔔 Dars eslatmalari olish (30 daqiqa oldin)
- 💬 Darsni baholash (dars tugagach 1-5 yulduz)
- 👤 Guruh o'zgartirish so'rovini yuborish (o'qituvchi tasdiqlaydi)

### 6.4 O'quvchi To'lov Holati
O'quvchi faqat o'z to'lov statusini ko'radi:
- ✅ To'langan — sana va summa
- ⏳ Kutilmoqda — tasdiqlash jarayonida
- ❌ To'lanmagan — eslatma va to'lov tugmasi

---

## 7. O'qituvchi Flow

### 7.1 Free Dars Taklifi
1. O'quvchi test ishlaydi → o'qituvchiga xabar keladi
2. Xabarda: o'quvchi ismi, natija (ball, daraja), telefon
3. O'qituvchi «Free darsga taklif qilish» tugmasini bosadi
4. Sana, vaqt, manzilni kiritadi
5. O'quvchiga avtomatik xabar ketadi

### 7.1.1 Bir nechta O'qituvchi Bosishi — Yechim

Bir xil darajadagi barcha o'qituvchilarga xabar bir vaqtda ketgani uchun, bir nechta o'qituvchi tugmani bosishi mumkin. Bunga qarshi:

- Tugma bosilganda backend **shartli update** qiladi: `UPDATE free_trial_requests SET teacher_id=X, status='invited' WHERE id=Y AND status='pending'`
- Bu — atomik DB operatsiyasi: faqat **birinchi bosgan** o'qituvchi uchun update muvaffaqiyatli o'tadi
- Boshqa o'qituvchilar bossa — update 0 qator qaytaradi → ularga *«Bu o'quvchi allaqachon [Ustoz ismi] tomonidan qabul qilindi»* ko'rsatiladi
- Qolgan o'qituvchilarning xabaridagi tugma bot tomonidan avtomatik tahrirlanadi/olib tashlanadi (`edit_message_reply_markup`)

### 7.2 To'lov Boshqaruvi (Bot orqali)

**Muhim: to'lov jarayonini O'QUVCHI boshlaydi, o'qituvchi/admin faqat TASDIQLAYDI.**

1. O'quvchi botda «💳 To'lov qilish» tugmasini bosadi (yoki `/pay`)
2. Faol guruhlar ro'yxati chiqadi (nomi + narxi bilan, tugmalar orqali)
3. O'quvchi guruhni tanlaydi
4. To'lov usulini tanlaydi: 💵 Naqd yoki 🌐 Online (Payme/Click/Uzum)
5. **Naqd tanlansa:**
   - Tizimda «kutilmoqda» (pending) holatda to'lov so'rovi yaratiladi
   - O'quvchiga: «Pulni o'qituvchingizga topshiring» xabari ko'rsatiladi
   - Guruhning o'qituvchisiga (agar biriktirilmagan bo'lsa — barcha adminlarga) xabar boradi: o'quvchi ismi, guruh, summa, «✅ Tasdiqlash» / «❌ Rad etish» tugmalari bilan
6. O'qituvchi/admin pulni qo'lda qabul qilib, «✅ Tasdiqlash» bosadi:
   - To'lov holati «tasdiqlangan» (confirmed) ga o'zgaradi
   - O'quvchi avtomatik ravishda guruhga ro'yxatga olinadi (`enrollments`)
   - O'quvchiga tasdiq xabari boradi: *«To'lovingiz tasdiqlandi ✅»*
7. «❌ Rad etish» bosilsa — o'quvchiga rad etilgani va o'qituvchi bilan bog'lanish tavsiyasi haqida xabar boradi

> ⚠️ **Atomiklik:** bir vaqtning o'zida ikki admin/o'qituvchi tasdiqlashga urinishi mumkin (masalan ikkalasi ham xabarni ko'rgan bo'lsa). Backend shartli update qiladi (`UPDATE payments SET status='confirmed' WHERE id=X AND status='pending'`) — faqat birinchisi muvaffaqiyatli bo'ladi, ikkinchisiga «Bu so'rov allaqachon ko'rib chiqilgan» ko'rsatiladi. Bu xuddi 7.1.1'dagi «birinchi bosgan g'olib» mexanizmi bilan bir xil.
> ⚠️ Payme/Click/Uzum avtomatik tasdiqlanadi (qo'lda tasdiqlash shart emas) — 3b-bosqich, alohida webhook integratsiyasi orqali.

### 7.3 Davomat
- Dars boshida guruhni tanlaydi
- Har bir o'quvchi: Keldi ✅ / Kelmadi ❌ / Kech qoldi ⏰
- Kelmagan o'quvchiga avtomatik xabar yuboriladi

### 7.4 Uy Vazifasi
- Guruhga uy vazifasi qo'shadi (matn, rasm, fayl, audio)
- Muddat: **keyingi dars sanasi va vaqti** (avtomatik taklif)
- Vazifa qo'shilganda barcha o'quvchilarga xabar ketadi

> ⚠️ Dars tugaganidan **3 soat** o'tib, agar uy vazifasi qo'shilmagan bo'lsa, o'qituvchiga eslatma: *«Guruh: [nom] uchun uy vazifasi qo'shilmagan. Qo'shishni unutdingizmi?»*
> ⚠️ Agar shu 3 soat ichida ham qo'shilmasa — **main admin/manager'ga** ham xabar boradi: *«⚠️ [O'qituvchi ismi] — [Guruh nomi] uchun uy vazifasini 3 soat ichida qo'shmadi.»*

### 7.5 Test Yaratish (Web App)
- Sertifikat turi: IELTS / CEFR
- Daraja: A1 — C2
- Savol turlari: MCQ, fill-in-the-blank, tarjima, audio
- Testni faollashtiradi — o'quvchilar uchun ko'rinadi

### 7.5.1 PDF'dan AI Orqali Test Yaratish

Qo'lda 20-40 ta savol kiritish o'rniga, o'qituvchi tayyor PDF fayl (masalan IELTS reading testi yoki o'zi tuzgan savollar) yuklab, testni AI yordamida avtomatik generatsiya qila oladi.

**Oqim:**
1. «Test yaratish» bo'limida o'qituvchi ikkita variantdan birini tanlaydi: ✍️ Qo'lda kiritish yoki 📄 PDF'dan yaratish
2. PDF faylni yuklaydi (matnli yoki skan — skan bo'lsa OCR orqali matn chiqariladi)
3. Matn AI'ga (Claude/GPT API) yuboriladi — **bitta chaqiruvda ikkita vazifa bajariladi**:
   - Savollarni, variantlarni va to'g'ri javoblarni structured JSON qilib ajratib olish (turi: MCQ / fill-in / tarjima / audio)
   - **Self-check** — AI o'zi natijasini tekshiradi: imlo xatosi bormi, to'g'ri javob asl matnga mos keladimi, savol formati tushunarlimi. Shubhali topilgan savolga **⚠️ warning** belgisi qo'yiladi
4. Natija **preview** sahifasida ko'rsatiladi — bu mavjud test-yaratish formasi, faqat maydonlar AI natijasi bilan **oldindan to'ldirilgan** (pre-filled)
5. ⚠️ warning belgili savollar preview'da ajratib/yuqorida ko'rsatiladi — bu savollarni o'qituvchi albatta ochib ko'rishi va tasdiqlashi (yoki tuzatishi) shart
6. Warning'siz (AI ishongan) savollarga o'qituvchi shunchaki ko'z yugurtiradi, xato ko'rsa xohlagan joyini to'g'ridan-to'g'ri formada tahrirlaydi yoki ✕ bilan o'chiradi
7. **Majburiy tekshiruv:** barcha ⚠️ warning belgili savollar «Ko'rdim» deb belgilanmaguncha «Faollashtirish» tugmasi disabled turadi
8. O'qituvchi «Saqlash va faollashtirish» bosgach, test oddiy test sifatida DB'ga yoziladi va o'quvchilar uchun ko'rinadi

> ℹ️ Test faollashtirilgandan keyin ham xato topilsa, istalgan vaqt tahrirlash mumkin — lekin bu o'zgarish o'quvchilar allaqachon topshirgan natijalarga (`test_results`) ta'sir qilmaydi, faqat keyin ishlaydiganlarga yangilangan versiya qo'llanadi.

> ⚠️ **DB:** `questions` jadvaliga `ai_generated BOOLEAN` va `needs_review BOOLEAN` (warning bayrog'i) maydonlari qo'shiladi. `tests` jadvaliga `source ENUM(manual, ai_pdf)` maydoni qo'shiladi.

### 7.6 Guruh O'zgartirish Tasdiqi
- O'quvchi so'rov yuboradi → o'qituvchiga xabar keladi
- O'qituvchi: Tasdiqlash ✅ yoki Rad etish ❌
- Tasdiqlansa — admin guruhni o'zgartiradi

---

## 8. Admin Flow

### 8.1 Admin Web App — Dashboard
- Real-time statistika: bugungi to'lovlar, yangi o'quvchilar, aktiv guruhlar
- Oylik daromad grafigi
- Tezkor harakatlar: yangi kurs, yangi guruh, broadcast

### 8.2 Kurs va Guruh Boshqaruvi
- Kurs: nom (3 tilda), tur (IELTS/CEFR/General), daraja, narx, davomiylik, rasm
- Guruh: kurs, o'qituvchi, jadval, xona, sig'im, boshlanish sanasi, Zoom linki
- Drag & drop dars jadvali

### 8.3 O'quvchi Boshqaruvi
- Ro'yxat, qidirish, filter (kurs, daraja, to'lov holati)
- Profil: test natijalari, to'lov tarixi, davomat, progress
- Guruhga qo'shish / o'zgartirish / chiqarish

### 8.4 To'lovlar
- Barcha to'lovlar ro'yxati
- Naqd to'lovlarni tasdiqlash / rad etish
- Qarzdorlar ro'yxati
- Moliya hisoboti — Excel / PDF eksport

### 8.5 Broadcast — Pro Funksiyalar
- **Auditoriya filtri:** barchaga / daraja bo'yicha / kurs bo'yicha / to'lamagan o'quvchilarga
- **Xabar turi:** matn, rasm, video, fayl, audio
- **Inline tugmalar:**
  - URL tugma — saytga, to'lov sahifasiga yo'naltirish
  - Callback tugma — botda javob kutish
  - To'lov tugmasi — to'g'ridan-to'g'ri to'lovga
  - Ko'p tugmali (2-3 tugma bir qatorda)
- Rejalashtirilgan xabar (scheduled)
- Preview ko'rish yuborishdan oldin
- Statistika: nechta yuborildi, ko'rildi

---

## 9. To'lov Tizimi

**Umumiy oqim:** to'lov so'rovini **har doim o'quvchi boshlaydi** (bot orqali guruh va usulni tanlab). O'qituvchi/admin faqat tasdiqlaydi (naqd) yoki tizim avtomatik tasdiqlaydi (online). Batafsil oqim — 7.2-bo'limda.

| Usul | Ishlash tartibi | Kim tasdiqlaydi |
|------|-----------------|-----------------|
| 💳 Payme | O'quvchi botda tanlaydi → to'laydi → avtomatik tasdiq | Tizim avtomatik |
| 💳 Click | O'quvchi botda tanlaydi → to'laydi → avtomatik tasdiq | Tizim avtomatik |
| 💳 Uzum Bank | O'quvchi botda tanlaydi → to'laydi → avtomatik tasdiq | Tizim avtomatik |
| 💵 Naqd (Cash) | O'quvchi botda so'rov yuboradi → ofisda pulni topshiradi → o'qituvchi/admin botda tasdiqlaydi | O'qituvchi / Admin |

**To'lov qoidalari:**
- Faqat to'liq to'lov (bo'lib to'lash yo'q)
- To'lov faqat FREE darsdan keyin amalga oshadi
- To'lov tasdiqlangach, o'quvchi avtomatik `enrollments` jadvaliga yoziladi (guruhga rasman qo'shiladi)

**Qaytarish (refund) jarayoni:**
- O'quvchi botda "Qaytarish so'rash" tugmasini bosadi → sababni yozadi → admin/manager'ga xabar ketadi
- Summa **avtomatik hisoblanadi** (admin tasdiqlaydi yoki o'zgartiradi):
  `refund_amount = to'langan_summa − (dars_narxi × qatnashgan_darslar_soni)`
  - `dars_narxi` — `courses.price_per_lesson` (DB'da, admin belgilaydi)
  - `qatnashgan_darslar_soni` — `attendance` jadvalidan olinadi
- Admin tasdiqlagach o'quvchiga xabar boradi, `refunds` jadvaliga yoziladi (12-bo'lim)

---

## 10. Test Tizimi — Web App

| Xususiyat | Tavsif |
|-----------|--------|
| Kirish vaqti | Istalgan vaqtda, bot menyusidan |
| Sertifikat turi | IELTS yoki CEFR |
| Daraja filtri | A1 / A2 / B1 / B2 / C1 / C2 |
| Tavsiya | O'quvchining joriy darajasi birinchi ko'rsatiladi |
| Testlar soni | Har daraja uchun bir nechta test |
| Savol turlari | MCQ, fill-in-the-blank, tarjima, audio |
| Natija | Ball, foiz, har savol uchun to'g'ri javob |
| O'qituvchi xabari | Test yakunida avtomatik xabar |

### Test Sahifalari

**Bosh sahifa:**
- IELTS / CEFR filtri
- Daraja filtri (o'quvchi darajasi avval)
- Testlar kartochkasi: nom, savollar soni, vaqt, oldingi natija

**Test ishlash:**
- Progress bar (1/20, 2/20...)
- Countdown timer
- MCQ: A/B/C/D tugmachalar
- Fill-in: matn input
- Translation: textarea
- Audio: player + javob input

**Natija sahifasi:**
- Umumiy ball va foiz
- Har savol: ✅ to'g'ri / ❌ noto'g'ri + to'g'ri javob
- «Yana ishlash» / «Bosh sahifaga» tugmalari

> ⚠️ Test yakunida o'qituvchiga xabar: *«👤 [Ism] — IELTS B2 testini yakunladi | 📊 85/100 (85%) | ⏱ 23 daqiqa»*

---

## 11. Web App Sahifalari

### Admin Web App
| Sahifa | Tarkib |
|--------|--------|
| Dashboard | Statistika, grafiklar, tezkor harakatlar |
| Kurslar | Ro'yxat, qo'shish, tahrirlash |
| Guruhlar | Ro'yxat, jadval, drag & drop |
| O'quvchilar | Ro'yxat, profil, guruh boshqaruvi |
| To'lovlar | Barcha to'lovlar, tasdiqlash, Excel/PDF |
| Broadcast | Xabar yaratish, inline tugmalar, statistika |
| O'qituvchilar | Ro'yxat, qo'shish, guruh biriktirish |
| Hisobot | Moliya, Excel/PDF yuklab olish |

### O'qituvchi Web App
| Sahifa | Tarkib |
|--------|--------|
| Guruhim | O'z guruhlari, o'quvchilar soni |
| Davomat | Guruh tanlash, belgilash, tarix |
| To'lovlar | Kim to'lagan/to'lamagan, naqd kiritish |
| Uy vazifasi | Mavjud vazifalar, yangi qo'shish |
| Test yaratish | Savol editoru, faollashtirish |
| O'quvchi profili | Daraja, davomat, test natijalari |

### O'quvchi Web App
| Sahifa | Tarkib |
|--------|--------|
| Testlar | Filtrlash, ishlash, natija va javoblar |
| Progress | Daraja, davomat %, test ball, grafiklar |
| Jadval | Haftalik dars jadvali, zoom linki |
| Uy vazifasi | Joriy va o'tgan vazifalar ro'yxati, fayllar |
| Profil | Ma'lumotlar, til, to'lov holati |

---

## 12. Database Modellari

### users
```
id              BIGINT PK       — Telegram user ID
full_name       VARCHAR(255)
username        VARCHAR(100)    — Telegram @username (profil/guruh linklari uchun)
phone           VARCHAR(20)
language        ENUM(uz,ru,en)
role            ENUM(student,teacher,manager,admin)
level           ENUM(A1,A2,B1,B2,C1,C2)
referral_code   VARCHAR(20)     — Unikal kod
referred_by     BIGINT FK
referral_bonus_given BOOLEAN
is_active       BOOLEAN
created_at      TIMESTAMP
```

### courses
```
id              SERIAL PK
title           JSONB           — {uz, ru, en}
type            ENUM(IELTS,CEFR,General)
level           ENUM(A1..C2)
description     JSONB           — 3 tilda
duration_months INTEGER
price           DECIMAL(10,2)
price_per_lesson DECIMAL(10,2)   — Refund hisob-kitobi uchun (12-bo'lim)
image_file_id   VARCHAR(255)
is_active       BOOLEAN
```

### groups
```
id              SERIAL PK
course_id       INT FK
teacher_id      BIGINT FK
name            VARCHAR(100)
schedule        JSONB           — [{day: 1, time: "18:00"}, ...]
room            VARCHAR(100)
group_chat_link VARCHAR(500)    — Guruh Telegram chat/kanal havolasi (Profilim'da ko'rsatiladi)
max_students    INTEGER
start_date      DATE
end_date        DATE
zoom_link       VARCHAR(500)
is_active       BOOLEAN
```

### free_trial_requests
```
id              SERIAL PK
student_id      BIGINT FK
test_result_id  INT FK
teacher_id      BIGINT FK
group_id        INT FK
trial_date      TIMESTAMP
location        VARCHAR(255)
status          ENUM(pending,invited,attended,declined,enrolled)
student_rating  SMALLINT        — 1-5 yulduz
student_feedback TEXT
created_at      TIMESTAMP
```

### enrollments
```
id              SERIAL PK
student_id      BIGINT FK
group_id        INT FK
free_trial_id   INT FK
status          ENUM(active,waiting,completed,dropped)
enrolled_at     TIMESTAMP
completed_at    TIMESTAMP
```

### payments
```
id              SERIAL PK
enrollment_id   INT FK
amount          DECIMAL(10,2)
provider        ENUM(payme,click,uzum,cash)
status          ENUM(pending,paid,refunded,failed)
transaction_id  VARCHAR(255)    — Online to'lovlar uchun
confirmed_by    BIGINT FK       — Naqd uchun
note            TEXT
paid_at         TIMESTAMP
```

### homeworks
```
id              SERIAL PK
group_id        INT FK
teacher_id      BIGINT FK
lesson_date     DATE
title           VARCHAR(255)
description     TEXT
file_id         VARCHAR(255)
due_date        TIMESTAMP       — Keyingi dars vaqti
reminder_sent   BOOLEAN         — O'qituvchiga eslatma yuborilganmi
created_at      TIMESTAMP
```

### tests
```
id              SERIAL PK
title           JSONB           — 3 tilda
type            ENUM(IELTS,CEFR)
level           ENUM(A1..C2)
created_by      BIGINT FK
time_limit_min  INTEGER         — 0 = cheksiz
passing_score   DECIMAL(5,2)    — O'tish bali (%); free dars yozilishida daraja aniqlash uchun (6.1.1)
is_active       BOOLEAN
```

### questions
```
id              SERIAL PK
test_id         INT FK
order_num       INTEGER
type            ENUM(mcq,fill_blank,translation,audio)
question        JSONB           — 3 tilda
options         JSONB           — MCQ uchun
correct_answer  TEXT
audio_file_id   VARCHAR(255)
points          INTEGER         — Standart: 1
```

### test_results
```
id              SERIAL PK
test_id         INT FK
student_id      BIGINT FK
score           INTEGER
max_score       INTEGER
percentage      DECIMAL(5,2)
answers         JSONB
started_at      TIMESTAMP
finished_at     TIMESTAMP
```

### waiting_list
```
id              SERIAL PK
student_id      BIGINT FK
group_id        INT FK
requested_at    TIMESTAMP
notified        BOOLEAN         — Joy bo'shaganda xabar berildimi
```

### refunds
```
id              SERIAL PK
payment_id      INT FK
student_id      BIGINT FK
reason          TEXT
requested_at    TIMESTAMP
status          ENUM(pending,approved,rejected)
approved_by     BIGINT FK
refund_amount   DECIMAL(10,2)
processed_at    TIMESTAMP
```

### referral_bonuses
```
id                  SERIAL PK
referrer_id         BIGINT FK
referred_student_id BIGINT FK
bonus_percent       DECIMAL(5,2)    — Standart: 5
applied_month       DATE
status              ENUM(pending,applied)
```

### center_settings
```
id              SERIAL PK
contact_phone   VARCHAR(20)
contact_username VARCHAR(100)    — Admin/markaz Telegram @username
address         JSONB           — {uz, ru, en}
updated_by      BIGINT FK
updated_at      TIMESTAMP
```
> ℹ️ Bog'lanish bo'limidagi (16.2) barcha kontakt ma'lumotlari shu jadvaldan o'qiladi — admin panelda o'zgartiriladi, kodga qayta tegilmaydi.

### support_chats
```
id              SERIAL PK
student_id      BIGINT FK
admin_id        BIGINT FK       — Javob berayotgan admin/manager
status          ENUM(open,closed)
last_message_by ENUM(student,admin)
last_message_at TIMESTAMP
created_at      TIMESTAMP
closed_at       TIMESTAMP
closed_reason   ENUM(resolved,timeout)   — timeout = 15 daqiqa javobsizlik
```

---

## 13. Avtomatik Eslatmalar

| Hodisa | Qabul qiluvchi | Vaqt | Mazmun |
|--------|---------------|------|--------|
| Dars eslatmasi | O'quvchi | 30 daq oldin | Bugun soat [vaqt] da dars bor 📚 |
| Uy vazifasi qo'shildi | O'quvchilar | Darhol | Yangi uy vazifasi: [sarlavha] |
| Uy vazifasi eslatma | O'qituvchi | Dars + 3 soat | ⚠️ Uy vazifasi qo'shilmagan |
| Uy vazifasi eslatma (admin) | Admin/Manager | Dars + 3 soat, hali qo'shilmasa | ⚠️ [O'qituvchi] uy vazifasini qo'shmadi |
| To'lov tasdiqlandi | O'quvchi | Darhol | To'lovingiz tasdiqlandi: [summa] ✅ |
| To'lov muddati | O'quvchi | 1 kun oldin | Ertaga to'lov muddati |
| Test natijasi | O'qituvchi | Darhol | [Ism] testni ishladi — [ball] |
| Free dars taklifi | O'quvchi | O'qituvchi bosganda | Sana, vaqt, manzil |
| Guruh o'zgartirish | O'qituvchi | Darhol | [Ism] guruh o'zgartirish so'radi |
| Kelmagan o'quvchi | O'quvchi | Davomat qo'yilganda | Bugun darsda bo'lmadingiz |
| Referal bonus | Taklif qilgan | Do'st o'qishni boshlaganda | Bonus berildi ✅ |
| Kurs tugadi | O'quvchi | Oxirgi dars | Sertifikatingiz tayyor 🎓 |
| Muloqot yopildi | O'quvchi + Admin | 15 daq javobsizlik | ⏱ Muloqot javobsizlik sababli yopildi |

---

## 14. Referal Tizimi

- Har bir o'quvchi unikal referal kodiga ega
- Do'stiga kod yoki havola ulashadi
- Do'st FREE darsga boradi → to'lov qiladi → o'qishni **RASMIY BOSHLAYDI**
- Faqat shundan keyin — taklif qilganga bonus beriladi

> ⚠️ Bonus FAQAT do'st to'lov qilib, rasmiy o'qishni boshlagandan keyin beriladi.

### 14.1 Bonus — Foizli Chegirma Tizimi

- Har bir muvaffaqiyatli taklif uchun referrer'ga **+5% chegirma** qo'shiladi (miqdor DB'da sozlanadi)
- Bonuslar **jamlanadi**: 2 ta do'st = 10% chegirma, 3 ta do'st = 15% va h.k.
- Jamlangan foiz **keyingi oy to'lovi** hisoblanganda avtomatik ayiriladi
- DB: `referral_bonuses` jadvali — `id, referrer_id, referred_student_id, bonus_percent (default 5), applied_month, status(pending/applied)`

---

## 15. Gamification

| Badge | Shart | Mukofot |
|-------|-------|---------|
| 🏅 Starter | Birinchi testni ishlash | Badge |
| ⭐ Top Student | 3 ta testda 90%+ | Badge + reyting |
| 📅 Regular | 10 ta darsga ketma-ket kelish | Badge |
| 👥 Ambassador | 1 kishi taklif va o'qishni boshlaydi | Bonus + Badge |
| 🎯 Level Up | Keyingi daraja testini topshirish | Badge |
| 📝 Diligent | 5 ta uy vazifasi o'z vaqtida | Badge |
| 🎓 Graduate | Kursni tugatish | Sertifikat + Badge |

---

## 16. Bot Menyu — 3 Tilda

| Tugma (UZ) | Tugma (RU) | Tugma (EN) | Funksiya |
|------------|------------|------------|---------|
| 📚 Kurslar | 📚 Курсы | 📚 Courses | Faol kurslar, guruh/o'qituvchi/jadval (16.3) |
| 🎯 Testlar | 🎯 Тесты | 🎯 Tests | Test ishlash (Web App) |
| 📋 Uy Vazifam | 📋 Домашнее задание | 📋 Homework | Vazifalar ro'yxati (16.4) |
| 📅 Jadvalim | 📅 Расписание | 📅 My Schedule | Haftalik jadval |
| 👤 Profilim | 👤 Мой профиль | 👤 My Profile | Profil kartasi (16.1) |
| 📊 Progress | 📊 Прогресс | 📊 Progress | Statistika (Web App) |
| 🏆 Reyting | 🏆 Рейтинг | 🏆 Ranking | Guruh TOP-10 |
| 👥 Referal | 👥 Реферал | 👥 Referral | Taklif havolasi |
| 🌐 Til | 🌐 Язык | 🌐 Language | Tilni o'zgartirish |
| 📞 Bog'lanish | 📞 Контакты | 📞 Contact | Admin kontakt + jonli savol-javob (16.2) |
| 📝 Free darsga yozilish | 📝 Запись на бесплатный урок | 📝 Book free lesson | Daraja tanlab, mos test topilguncha (6.1.1) |

### 16.1 Profilim

**Agar o'quvchi hech qanday kursda o'qimasa:**
- Profil ma'lumotlari chiroyli, stiker/emoji bilan bezatilgan kartochka ko'rinishida chiqadi: 👤 Ism, 📱 Telefon, 🌐 Til, 📅 Ro'yxatdan o'tgan sana, 🎁 Referal kod
- Pastda: *«Siz hozircha hech qaysi kursga yozilmagansiz»* + «📝 Free darsga yozilish» tugmasi

**Agar o'quvchi biror kursda o'qisa, qo'shimcha ko'rsatiladi:**
- 📚 Kurs nomi va darajasi
- 👨‍🏫 O'qituvchi — ismi, **Telegram username'iga link** qilib (`t.me/{username}`, `users.username` dan)
- 👥 Guruh — nomi va **guruh chatiga havola** (`groups.group_chat_link`)
- 💳 To'lov holati (6.4 bilan bog'liq)

### 16.2 Bog'lanish

- Tugma bosilganda admin/markaz kontaktlari **bazadan** (`center_settings`) chiqariladi: ☎️ Telefon, ✍️ Username, 📍 Manzil — shu jadval admin panelda tahrirlansa, botda darhol yangilanadi, kodga tegish shart emas
- Shu yerning o'zida **«❓ Savol berish»** tugmasi bo'ladi:
  1. O'quvchi savolini yozadi → xabar admin(lar)ga yuboriladi, `support_chats` yozuvi ochiladi (`status='open'`)
  2. Admin javob yozsa — bot javobni o'quvchiga proksi qiladi (ikkala tomon ham bot ichida yozishadi, bir-birining raqamini ko'rmaydi)
  3. **15 daqiqa** — agar shu vaqt ichida ikkala tomondan biri ham javob yozmasa, tizim suhbatni avtomatik yopadi (`status='closed', closed_reason='timeout'`) va **ikkala tarafga ham** xabar boradi: *«⏱ Muloqot 15 daqiqa javobsizlik sababli yopildi»*
  4. Savol hal bo'lsa, admin «Yakunlash» tugmasi bilan ham yopishi mumkin (`closed_reason='resolved'`)

### 16.3 Kurslar

- Tugma bosilganda **faol kurslar ro'yxati inline tugmalar** ko'rinishida chiqadi (har bir kurs — alohida tugma)
- Kursni tanlaganda, shu kursning barcha faol guruhlari tartib bilan ko'rsatiladi:
  - 👥 Guruh nomi
  - 👨‍🏫 O'qituvchi (ismi + username link)
  - 🗓 Jadval — kunlar va vaqt (`groups.schedule`)
  - 🪑 Joylar — band/bo'sh soni (`max_students` va joriy o'quvchilar soni)
- Har bir guruh ostida **«Free darsga yozilish»** tugmasi — bosilsa 6.1.1/6.2 flow'i boshlanadi

### 16.4 Uy Vazifam

**Agar o'quvchi hech qanday guruhda o'qimasa** (faol `enrollment`i yo'q bo'lsa):
- Uy vazifasi ro'yxati o'rniga: *«📚 Siz hozircha hech qaysi kursda o'qimayapsiz»* + **«📝 Free darsga yozilish»** tugmasi ko'rsatiladi (bosilsa 6.1.1 flow'i boshlanadi)

**Agar o'quvchi faol guruhda o'qisa:**
- Shu guruhga tegishli uy vazifalari ro'yxati chiqadi (`homeworks` jadvalidan, `group_id` bo'yicha) — sarlavha, tavsif, fayl (agar bo'lsa), muddati
- O'qituvchi yangi uy vazifa qo'shganda, guruhdagi barcha o'quvchilarga **darhol** avtomatik xabar boradi: *«📋 Yangi uy vazifasi qo'shildi: [sarlavha]»* (bu allaqachon 13-bo'limdagi Avtomatik Eslatmalar jadvalida bor)

> ℹ️ **Materiallar** tugmasi bekor qilindi — uning o'rniga «Uy Vazifam» ishlatiladi (fayl/PDF/audio yuborish kerak bo'lsa, o'qituvchi shuni ham uy vazifasiga fayl sifatida biriktiradi, `homeworks.file_id`).

---

## 17. Sertifikat Tizimi

- Kurs tugagach avtomatik PDF sertifikat generatsiya
- IELTS kurslari uchun IELTS formatiga mos dizayn
- CEFR kurslari uchun CEFR darajasi ko'rsatilgan dizayn
- O'quvchi PDF formatida yuklab oladi

---

## 18. Xavfsizlik

- Rate limiting — spam himoya
- **Admin buyruqlar faqat DB'dagi `users.role IN (admin, manager)` bo'lgan Telegram ID lardan** — `.env` fayldagi qattiq yozilgan (hardcoded) ID lar ishlatilmaydi, chunki yangi adminlar qo'shilishi yoki olib tashlanishi mumkin. Super Admin botdan/panel orqali admin qo'sha/o'chira oladi, o'zgarish darhol kuchga kiradi (qayta deploy shart emas)
- Web App — Telegram initData orqali autentifikatsiya (HMAC)
- To'lov webhook lar HTTPS va imzo tekshiruvi
- SQLAlchemy ORM — SQL injection himoya
- Bot webhook faqat HTTPS

---

## 18.1 Monitoring va Backup

- **DB backup** — PostgreSQL har kuni avtomatik zaxira nusxa oladi (masalan, xatolik yoki ma'lumot yo'qolishi holatida oldingi kunga qaytarish imkoni bo'lishi uchun)
- **Error tracking** — production xatolari (bot crash, to'lov xatosi va h.k.) haqida avtomatik xabar beruvchi tizim ulanadi (masalan Sentry), shunda muammo darhol ma'lum bo'ladi, kunlab bilinmay qolmaydi

---

## 19. Tayyor Deb Hisoblaymiz Qachonki

**O'quvchi:**
1. Test ishlaydi, daraja aniqlanadi
2. O'qituvchidan free dars taklifi keladi
3. To'lov qiladi → xabar keladi
4. Guruhga qo'shiladi, jadval va materiallar ko'rinadi
5. Uy vazifasini ko'radi

**O'qituvchi:**
1. Test natijasi xabari keladi → free darsga taklif qiladi
2. Davomat qo'yadi
3. Uy vazifasi qo'shadi, 1 soat eslatmasi ishlaydi
4. Naqd to'lovni bot orqali kiritadi

**Admin:**
1. Web App da to'liq boshqaruv ishlaydi
2. Broadcast inline tugmalar bilan ishlaydi
3. Moliya hisoboti Excel/PDF da chiqadi
4. 3 tilda barcha interfeys ishlaydi

---

## 20. Loyiha Bosqichlari (Roadmap)

| Bosqich | Tarkib | Muddat |
|---------|--------|--------|
| 1 — Bot MVP | Ro'yxat, til, asosiy menyu, DB | 1-2 hafta |
| 2 — Test + Free dars | Web App testlar, free dars flow | 2-3 hafta |
| 3 — To'lov | Payme, Click, Uzum, naqd | 1-2 hafta |
| 4 — O'qituvchi panel | Davomat, uy vazifasi, to'lovlar | 1-2 hafta |
| 5 — Admin Web App | Dashboard, broadcast, hisobot | 2-3 hafta |
| 6 — Gamification | Badge, reyting, referal, sertifikat | 1-2 hafta |
| 7 — Polishing | 3 til test, UI/UX, load test | 1 hafta |

---

*TZ v2.6 — English Center Bot*

---

## O'zgarishlar Jurnali (v2.5 → v2.6)

1. **Test yaratish (7.5.1)** — yangi bo'lim: o'qituvchi PDF yuklab, AI yordamida testni avtomatik generatsiya qila oladi (qo'lda kiritishga alternativ variant)
2. AI bitta chaqiruvda savollarni ajratib oladi **va self-check qiladi** (imlo, javob to'g'riligi, matnga moslik) — shubhali savollarga `needs_review` (⚠️ warning) bayrog'i qo'yiladi, alohida ikkinchi tekshiruv bosqichi yo'q
3. Natija preview'da (mavjud test-yaratish formasi, pre-filled holda) ko'rsatiladi; ⚠️ warning belgili savollarni ko'rib chiqish **majburiy** — aks holda «Faollashtirish» tugmasi disabled
4. Test faollashgandan keyin ham tahrirlash mumkin, lekin bu allaqachon topshirilgan `test_results`ga ta'sir qilmaydi
5. DB: `questions.ai_generated`, `questions.needs_review`, `tests.source (manual/ai_pdf)` maydonlari qo'shildi

## O'zgarishlar Jurnali (v2.0 → v2.1)

1. Free dars taklifida bir nechta o'qituvchi bosishi muammosi — atomik "birinchi bosgan g'olib" mexanizmi qo'shildi (7.1.1)
2. Main menyuga «Free darsga yozilish» tugmasi qo'shildi (6.1.1)
3. Guruh to'lganda boshqa guruh tavsiyasi yoki kutish ro'yxati (6.2.1), `waiting_list` jadvali qo'shildi
4. Refund (qaytarish) jarayoni uchun `refunds` jadvali va oqim qo'shildi
5. Referal bonusi — jamlanadigan foizli chegirma tizimi (14.1), `referral_bonuses` jadvali qo'shildi
6. Uy vazifasi muddati 1 soatdan 3 soatga o'zgartirildi, admin/manager'ga eskalatsiya qo'shildi
7. Monitoring va backup bo'yicha yangi bo'lim qo'shildi (18.1)

## O'zgarishlar Jurnali (v2.1 → v2.2)

1. «Free darsga yozilish» flow'i to'g'rilandi — endi testsiz emas: o'quvchi darajasini tanlaydi → mos test beriladi → o'tsa shu guruh, o'ta olmasa avtomatik pastroq daraja testi taklif qilinadi (6.1.1); `tests.passing_score` maydoni qo'shildi, `is_head_teacher` olib tashlandi
2. Guruh to'lganda **avval boshqa guruh tavsiya qilinadi**, kutish ro'yxati faqat mutlaqo bo'sh guruh topilmasa ishlatiladi (6.2.1)
3. Refund summasi uchun aniq formula qo'shildi: to'langan summa − (dars narxi × qatnashgan darslar soni); `courses.price_per_lesson` maydoni qo'shildi

## O'zgarishlar Jurnali (v2.2 → v2.3)

1. **Profilim (16.1)** — kursda o'qimasa chiroyli/stikerli profil kartochkasi; kursda o'qisa kurs nomi + o'qituvchi va guruh Telegram linklari ko'rsatiladi. `users.username`, `groups.group_chat_link` maydonlari qo'shildi
2. **Bog'lanish (16.2)** — admin kontaktlari endi `.env`/kod emas, **`center_settings` jadvalidan** o'qiladi (admin panelda tahrirlanadi); shu bo'limda jonli «Savol berish» chat qo'shildi — 15 daqiqa ikkala tomondan javob bo'lmasa, suhbat avtomatik yopiladi va ikkala tarafga xabar boradi. `support_chats` jadvali qo'shildi
3. **Kurslar (16.3)** — faol kurslar inline tugmalar bilan, har bir guruh uchun o'qituvchi, jadval, bo'sh joylar tartibli ko'rinishda chiqadi
4. **Adminlar boshqaruvi** — admin/manager ID'lari endi `.env`dan emas, **DB'dan (`users.role`)** o'qiladi, shunda yangi admin qo'shish/o'chirish qayta deploy talab qilmaydi (18-bo'lim)
5. 13-bo'limdagi uy vazifasi eslatma jadvali 3 soatlik muddat va admin eskalatsiyasiga mos yangilandi, 15 daqiqalik muloqot-yopilish eslatmasi qo'shildi

## O'zgarishlar Jurnali (v2.3 → v2.4)

1. **«📁 Materiallar» tugmasi bekor qilindi** — o'rniga «Uy Vazifam» ishlatiladi (16.4). Fayl/PDF/audio kerak bo'lsa, o'qituvchi shuni uy vazifasiga biriktiradi (`homeworks.file_id`)
2. **Uy Vazifam (16.4)** — agar o'quvchi hech qanday guruhda o'qimasa, vazifalar o'rniga «Siz hali o'qimaysiz» xabari va «Free darsga yozilish» tugmasi ko'rsatiladi; faol guruhda o'qisa — shu guruhga tegishli vazifalar ro'yxati chiqadi
3. O'quvchi Web App'dagi «Materiallar» sahifasi olib tashlandi, «Uy vazifasi» sahifasi bilan almashtirildi (11-bo'lim)
