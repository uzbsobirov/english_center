"""
PDF'dan AI orqali test yaratish xizmati (TZ v2.6, 7.5.1-bo'lim).
- PDF matnini ajratish (pypdf layout va tozalash bilan)
- Kengaytirilgan parser: Har qanday savol (1., Q1, Question 1) va variant (A), A., (A), a)) formatlarini taniydi
- Kalitlar (Answer Key) bo'limini avtomatik ajratib olib, to'g'ri javoblarni biriktiradi
- Tashqi AI (Gemini / OpenAI) kalitlari mavjud bo'lsa, avtomatik LLM tahlili
- Self-check: Shubhali yoki kam variantli savollarga `needs_review=True` (⚠️ warning) belgisini qo'yish
"""
import io
import os
import re
import json
from typing import Any

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import pypdf
except ImportError:
    pypdf = None


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """PDF baytlaridan matnni ajratib oladi va tartibli tozalaydi."""
    if pypdf is None:
        return "PDF kutubxonasi mavjud emas."

    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text_chunks = []
        for page in reader.pages:
            txt = None
            try:
                # 1. Avval layout saqlangan holda sinab ko'ramiz
                txt = page.extract_text(extraction_mode="layout")
            except Exception:
                pass
            if not txt or len(txt.strip()) < 10:
                txt = page.extract_text() or ""
            if txt:
                text_chunks.append(txt)

        full_text = "\n\n".join(text_chunks)

        # 2. Tozalash va normalizatsiya
        full_text = full_text.replace('\xa0', ' ').replace('\u2013', '-').replace('\u2014', '-')
        full_text = full_text.replace('“', '"').replace('”', '"').replace('’', "'")
        
        # Chiziqcha bilan bo'lingan so'zlarni birlashtirish (masalan: differ-\nent -> different)
        full_text = re.sub(r'(\b\w+)-\n(\w+\b)', r'\1\2', full_text)
        
        # Boshqaruv belgilarini tozalash
        cleaned = re.sub(r"\r\n|\r", "\n", full_text)
        
        # Sahifa raqamlari va keraksiz sarlavhalarni tozalash
        cleaned = re.sub(r"(?i)\bpage\s+\d+\s*(?:of\s*\d+)?\b", "", cleaned)
        cleaned = re.sub(r"(?i)\bcambridge\s+(?:english|university\s+press)[\w\s\d]*\b", "", cleaned)

        return cleaned
    except Exception as e:
        print(f"⚠️ PDF extract error: {e}")
        return ""


def _extract_and_strip_answer_keys(text: str) -> tuple[str, dict[int, str]]:
    """
    Matn oxiridagi javoblar kalitini topadi va uni asosiy matndan ajratib oladi.
    """
    answer_keys = {}
    key_pattern = r'(?i)(?:\n|^)(?:answers?|answer\s*key|keys?|correct\s*answers?|javoblar)[\s\:\-]+(.*?)(?:\Z)'
    key_match = re.search(key_pattern, text, re.DOTALL)
    
    if key_match:
        key_text = key_match.group(1)
        pairs = re.findall(r'(\d+)[\.\s\:\-\)]+([A-Za-z0-9_\-\s\']+?)(?=(?:,\s*\d+[\.\-\s\:\)]|\s+\d+[\.\-\s\:\)]|\n|$))', key_text)
        for q_num, ans in pairs:
            clean_ans = ans.strip()
            if clean_ans and len(clean_ans) < 50:
                answer_keys[int(q_num)] = clean_ans
        # Savollar matnidan javoblar kalitini qirqib olamiz
        text = text[:key_match.start()]

    return text, answer_keys


async def _try_llm_generation(raw_text: str, cert_type: str, level: str) -> list[dict[str, Any]] | None:
    """
    Agar GEMINI_API_KEY yoki OPENAI_API_KEY bo'lsa, LLM orqali barcha turdagi savollarni (MCQ, True/False, Fill Blank, Short Answer) chiqaradi.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not gemini_key and not openai_key:
        return None

    prompt = f"""
Siz ingliz tili bo'yicha professional imtihon tuzuvchi va tahlilchisiz (IELTS, CEFR, Cambridge).
Quyidagi matndan {cert_type} ({level}) darajasiga oid BARCHA test savollarini ajratib oling va JSON formatida qaytaring.

O'TA MUHIM QOIDALAR (PASSAGE BIRIKTIRISH VA CHIZIQLARNI TOZALASH):
1. **Passage (O'qish matni) ni barcha tegishli savollarga biriktirish:**
   Agar biror matn (Reading passage), dialog, hikoya yoki jadval bir nechta savolga (masalan 1- va 2-savollarga) tegishli bo'lsa, O'SHA MATNNI USHBU SAVOLLARNING HAR BIRINING "text" QISMIGA TO'LIQ QO'SHING!
   Format:
   "text": "📖 Passage:\\n[O'qish matni to'liq]\\n\\n❓ Question:\\n[Savol matni]"
   Shunda o'quvchi har bir savolni ishlayotganda unga tegishli matnni to'liq ko'rib turadi.

2. **Qog'ozdagi javob yozish chiziqlarini (_____) tozalash:**
   Qog'ozdagi testlarda ochiq savollardan keyin qalam bilan yozish uchun qo'yilgan bo'sh chiziqlar (masalan: `________________`, `----------------`, `................`) bo'ladi.
   BU QOG'OZ CHIZIQLARINI SAVOL MATNIGA ASLO QO'SHMANG! Ularni butunlay tozalab tashlang.
   Savol turi esa "short_answer" bo'ladi (chunki o'quvchi webapp orqali matn yozadi).

3. **Savol turlari ("type"):**
   - "mcq" — Variantli savollar. "options" massivida variantlar (A, B, C, D) bo'lsin.
   - "true_false" — To'g'ri / Noto'g'ri. "options": ["True", "False"].
   - "fill_blank" — Gap ichidagi bo'sh joyni to'ldirish (gap ichidagi bitta `___`).
   - "short_answer" — Ochiq yozma savollar (qog'ozdagi chiziqli javob joylari bor savollar). "options": [].

4. **To'g'ri javob:** Matndagi Answer Key yoki matn mantiqiga asoslanib "correct_answer" maydoniga to'g'ri javobni yozing.

JSON sxemasi:
[
  {{
    "order_num": 1,
    "type": "mcq" | "true_false" | "fill_blank" | "short_answer",
    "text": "📖 Passage:\\n...\\n\\n❓ Question:\\n...",
    "options": ["A) ...", "B) ..."] yoki ["True", "False"] yoki [],
    "correct_answer": "...",
    "needs_review": false
  }}
]

Faqat toza JSON array qaytaring. Boshqa hech qanday so'z yoki markdown yozmang.

Matn:
{raw_text[:100000]}
"""

    if gemini_key and aiohttp is not None:
        gemini_models = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3-flash-preview", "gemini-2.5-pro", "gemini-flash-latest"]
        for g_model in gemini_models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{g_model}:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 8192}
                }
                async with aiohttp.ClientSession() as client:
                    async with client.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=45)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            text_out = data["candidates"][0]["content"]["parts"][0]["text"]
                            text_out = re.sub(r"^```json\s*", "", text_out.strip())
                            text_out = re.sub(r"\s*```$", "", text_out.strip())
                            parsed = json.loads(text_out)
                            if isinstance(parsed, list) and len(parsed) > 0:
                                for idx, q in enumerate(parsed, 1):
                                    q["id"] = f"q_ai_{idx}"
                                    q["order_num"] = idx
                                    q["type"] = q.get("type", "mcq")
                                    if q["type"] == "mcq" and not q.get("options"):
                                        q["type"] = "short_answer"
                                    q["points"] = 1
                                    q["ai_generated"] = True
                                return parsed
            except Exception as e:
                print(f"⚠️ Gemini API model {g_model} fallback: {e}")
                continue

    if openai_key and aiohttp is not None:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }
            async with aiohttp.ClientSession() as client:
                async with client.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=35)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content_str = data["choices"][0]["message"]["content"]
                        parsed = json.loads(content_str)
                        if isinstance(parsed, dict) and "questions" in parsed:
                            parsed = parsed["questions"]
                        if isinstance(parsed, list) and len(parsed) > 0:
                            for idx, q in enumerate(parsed, 1):
                                q["id"] = f"q_ai_{idx}"
                                q["order_num"] = idx
                                q["type"] = q.get("type", "mcq")
                                if q["type"] == "mcq" and not q.get("options"):
                                    q["type"] = "short_answer"
                                q["points"] = 1
                                q["ai_generated"] = True
                            return parsed
        except Exception as e:
            print(f"⚠️ OpenAI API fallback to regex: {e}")

    return None


async def generate_test_from_pdf_text(
    raw_text: str,
    cert_type: str = "IELTS",
    level: str = "B1",
) -> list[dict[str, Any]]:
    """
    Matnni tahlil qilib, variantli (MCQ), True/False, Bo'sh joy to'ldirish (Fill Blank)
    va Ochiq qisqa javob (Short Answer) savollarini to'liq ajratib oladi.
    """
    # 1. Agar LLM mavjud bo'lsa, birinchi o'rinda AI dan foydalanamiz
    llm_res = await _try_llm_generation(raw_text, cert_type, level)
    if llm_res:
        return llm_res

    # 2. Kalitlar bo'limini ajratish va tozalash
    cleaned_text, answer_keys = _extract_and_strip_answer_keys(raw_text)

    # 3. Savollarni raqamlar bo'yicha ajratish (1., 1), Q1., Question 1:)
    q_blocks = re.split(r'(?:\n|^)(?:Question\s*|Q\s*)?(\d+)[\.\)\:\-\s]\s+', cleaned_text)
    questions = []

    # Agar 1-savoldan oldin umumiy matn (Passage) bo'lsa, uni ajratib olamiz
    common_passage = q_blocks[0].strip() if len(q_blocks) > 1 and len(q_blocks[0].strip()) > 30 else ""

    if len(q_blocks) > 1:
        for i in range(1, len(q_blocks), 2):
            q_num = int(q_blocks[i])
            content = q_blocks[i+1].strip()
            if not content:
                continue

            # Qog'ozdagi javob chiziqlarini (_______, -------, ......) tozalaymiz
            content_cleaned = re.sub(r'(?:\n|^)\s*[\_\-\.]{5,}\s*', '', content).strip()

            # Variantlarni topamiz (A), A., [A], a), A )
            opt_matches = list(re.finditer(r'(?:^|\s{2,}|\n)(?:\(([A-Ea-e])\)|\[([A-Ea-e])\]|([A-Ea-e])[\.\)\:\-\s])\s*([^\n\r]+?)(?=(?:\s{2,}(?:\([A-Ea-e]\)|\[[A-Ea-e]\]|[A-Ea-e][\.\)\:\-\s])|\n(?:\([A-Ea-e]\)|\[[A-Ea-e]\]|[A-Ea-e][\.\)\:\-\s])|\Z))', content_cleaned))

            # 1-Holat: Multiple Choice (Variantli) savol
            if opt_matches and len(opt_matches) >= 2:
                first_opt_start = opt_matches[0].start()
                q_text = content_cleaned[:first_opt_start].strip() if first_opt_start > 0 else content_cleaned.split('\n')[0].strip()
                q_text = re.sub(r"^[\d\.\)\:\-\s]+", "", q_text).strip()

                options = []
                for m in opt_matches:
                    letter = (m.group(1) or m.group(2) or m.group(3)).upper()
                    opt_val = m.group(4).strip()
                    options.append(f"{letter}) {opt_val}")

                correct_key = answer_keys.get(q_num)
                correct_ans = None
                if correct_key:
                    for opt in options:
                        if opt.upper().startswith(f"{correct_key.upper()})") or correct_key.upper() in opt.upper():
                            correct_ans = opt
                            break
                if not correct_ans:
                    correct_ans = options[0]

                needs_review = len(options) < 3 or len(q_text) < 6

                full_q_text = f"📖 Passage:\n{common_passage}\n\n❓ Question:\n{q_text}" if common_passage else q_text

                questions.append({
                    "id": f"q_{len(questions)+1}",
                    "order_num": len(questions)+1,
                    "type": "mcq",
                    "text": full_q_text or f"Savol #{q_num}",
                    "options": options,
                    "correct_answer": correct_ans,
                    "points": 1,
                    "ai_generated": True,
                    "needs_review": needs_review,
                })

            # 2-Holat: True / False (To'g'ri / Noto'g'ri) savoli
            elif re.search(r'(?i)\b(true\s*/\s*false|true\s+or\s+false|t\s*/\s*f|to\'g\'ri\s*/\s*noto\'g\'ri)\b', content_cleaned) or content_cleaned.lower().endswith(("(t/f)", "[t/f]")):
                q_text = re.sub(r"^[\d\.\)\:\-\s]+", "", content_cleaned).strip()
                q_text = re.sub(r'(?i)[\(\[]?(?:true\s*/\s*false|true\s+or\s+false|t/f|to\'g\'ri/noto\'g\'ri)[\)\]]?', '', q_text).strip()

                correct_val = answer_keys.get(q_num, "True")
                if correct_val.lower() in ("true", "t", "1", "to'g'ri"):
                    correct_val = "True"
                elif correct_val.lower() in ("false", "f", "0", "noto'g'ri"):
                    correct_val = "False"
                else:
                    correct_val = "True"

                full_q_text = f"📖 Passage:\n{common_passage}\n\n❓ Question:\n{q_text}" if common_passage else q_text

                questions.append({
                    "id": f"q_{len(questions)+1}",
                    "order_num": len(questions)+1,
                    "type": "true_false",
                    "text": full_q_text or f"Savol #{q_num}",
                    "options": ["True", "False"],
                    "correct_answer": correct_val,
                    "points": 1,
                    "ai_generated": True,
                    "needs_review": not bool(answer_keys.get(q_num)),
                })

            # 3-Holat: Fill in the Blanks (Bo'sh joyni to'ldirish)
            elif "___" in content_cleaned or "...." in content_cleaned or re.search(r"\bfill in\b", content_cleaned, re.IGNORECASE):
                q_text = re.sub(r"^[\d\.\)\:\-\s]+", "", content_cleaned).strip()
                correct_ans = answer_keys.get(q_num, "")

                full_q_text = f"📖 Passage:\n{common_passage}\n\n❓ Question:\n{q_text}" if common_passage else q_text

                questions.append({
                    "id": f"q_{len(questions)+1}",
                    "order_num": len(questions)+1,
                    "type": "fill_blank",
                    "text": full_q_text or f"Bo'sh joyni to'ldiring #{q_num}",
                    "options": [],
                    "correct_answer": correct_ans,
                    "points": 1,
                    "ai_generated": True,
                    "needs_review": not bool(correct_ans),
                })

            # 4-Holat: Short Answer / Ochiq savol (qog'ozdagi chiziqlar tozalangan)
            else:
                q_text = re.sub(r"^[\d\.\)\:\-\s]+", "", content_cleaned).strip()
                correct_ans = answer_keys.get(q_num, "")

                full_q_text = f"📖 Passage:\n{common_passage}\n\n❓ Question:\n{q_text}" if common_passage else q_text

                questions.append({
                    "id": f"q_{len(questions)+1}",
                    "order_num": len(questions)+1,
                    "type": "short_answer",
                    "text": full_q_text or f"Savol #{q_num}",
                    "options": [],
                    "correct_answer": correct_ans,
                    "points": 1,
                    "ai_generated": True,
                    "needs_review": not bool(correct_ans),
                })

    # Agar savollar topilmagan bo'lsa (yoki matn bloklari noaniq bo'lsa), matn asosida standart savollar generatsiya qilamiz
    if not questions:
        sentences = [s.strip() for s in re.split(r"[\.\?\!]\s+", cleaned_text) if len(s.strip()) > 15]
        for i in range(1, min(len(sentences) + 1, 6)):
            sent = sentences[i - 1] if i - 1 < len(sentences) else f"{cert_type} {level} Placement Question #{i}"
            words = sent.split()
            if len(words) >= 4:
                target_word = words[len(words) // 2]
                blank_text = sent.replace(target_word, "_______", 1)
                opts = [
                    f"A) {target_word}",
                    f"B) {target_word}ing",
                    f"C) {target_word}ed",
                    f"D) un{target_word}",
                ]
            else:
                blank_text = f"Choose the correct grammatical form: {sent}"
                opts = ["A) Option A", "B) Option B", "C) Option C", "D) Option D"]

            questions.append({
                "id": f"q_{i}",
                "order_num": i,
                "type": "mcq",
                "text": blank_text,
                "options": opts,
                "correct_answer": opts[0],
                "points": 1,
                "ai_generated": True,
                "needs_review": False,
            })

    return questions
