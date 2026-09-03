import os
import asyncio
import aiohttp
import json
import re
from dotenv import load_dotenv

load_dotenv()

async def test_exact_user_case():
    api_key = os.getenv("GEMINI_API_KEY")
    
    exact_pdf_text = """
    Remote work has changed the way many companies operate. While some employees appreciate the flexibility of working from home, others argue that face-to-face collaboration leads to better teamwork and faster decision-making. Several studies suggest that a hybrid model, combining remote and office work, may offer the best balance between productivity and employee satisfaction.

    1. According to the passage, what is suggested as a possible solution?
    A) Working from home full-time
    B) Working in the office full-time
    C) A hybrid model combining both
    D) Reducing working hours

    2. In your own words, explain one advantage and one disadvantage of remote work mentioned in the passage.
    ______________________________________________________________________
    ______________________________________________________________________
    ______________________________________________________________________
    """
    
    prompt = f"""
Siz ingliz tili bo'yicha professional test tuzuvchi va tahlilchisiz.
Quyidagi matndan test savollarini ajratib oling va JSON formatida qaytaring.

O'TA MUHIM 3 TA QOIDA:
1. **Passage (Matn) ni savollarga biriktirish:**
   Agar biror matn (Reading passage), dialog yoki hikoya 1 ta yoki bir nechta savolga (masalan 1- va 2-savollarga) tegishli bo'lsa, O'SHA MATNNI USHBU SAVOLLARNING HAR BIRINING TEXT QISMIGA TO'LIQ QO'SHING!
   Format:
   "text": "📖 Passage:\\n[O'qish matni]\\n\\n❓ Question:\\n[Savol matni]"
   Shunda o'quvchi har bir savolni ishlayotganda matnni ham birga ko'rib turadi.

2. **Qog'ozdagi javob chiziqlarini (_____) tozalash:**
   Qog'ozdagi testlarda ochiq savollardan keyin o'quvchi qalam bilan yozishi uchun qo'yilgan chiziqlar (masalan: `______`, `-------`, `......`) bo'ladi.
   BU CHIZIQLARNI SAVOL MATNIGA ASLO QO'SHMANG! Ularni butunlay tozalab tashlang.
   Savol turi esa "short_answer" bo'ladi (chunki o'quvchi webapp orqali matn yozadi).

3. **Savol turlari ("type"):**
   - "mcq" — Variantli savollar. "options" massivida 4 ta variant (A, B, C, D) bo'lsin.
   - "true_false" — To'g'ri / Noto'g'ri. "options": ["True", "False"].
   - "fill_blank" — Gap ichidagi bo'sh joyni to'ldirish (gap ichidagi bitta `___`).
   - "short_answer" — Ochiq yozma savollar (qog'ozdagi chiziqli javob joylari bor savollar). "options": [].

JSON sxemasi:
[
  {{
    "order_num": 1,
    "type": "mcq" | "true_false" | "fill_blank" | "short_answer",
    "text": "📖 Passage:\\n...\\n\\n❓ Question:\\n...",
    "options": ["A) ...", "B) ..."] yoki [],
    "correct_answer": "...",
    "needs_review": false
  }}
]

Faqat toza JSON array qaytaring. Boshqa so'z yozmang.

Matn:
{exact_pdf_text}
"""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 8192}
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            out = data["candidates"][0]["content"]["parts"][0]["text"]
            out = re.sub(r"^```json\s*", "", out.strip())
            out = re.sub(r"\s*```$", "", out.strip())
            parsed = json.loads(out)
            
            with open("scratch/user_test_out.json", "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=2, ensure_ascii=False)
            print("Successfully written to scratch/user_test_out.json")

if __name__ == "__main__":
    asyncio.run(test_exact_user_case())
