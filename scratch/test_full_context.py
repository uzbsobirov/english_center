import os
import asyncio
import aiohttp
import json
import re
from dotenv import load_dotenv

load_dotenv()

async def test_full_context_prompt():
    api_key = os.getenv("GEMINI_API_KEY")
    
    sample_pdf_text = """
    IELTS READING TEST — SECTION 1
    
    Instructions: You should spend about 20 minutes on Questions 1-5, which are based on Reading Passage 1 below.
    
    READING PASSAGE 1
    The Underwater Forests of California
    Giant kelp is the largest marine plant in the world. Found extensively along the coast of California, these underwater forests can grow up to 60 centimeters in a single day under optimal conditions of sunlight and cold, nutrient-rich water. Kelp forests provide shelter and food for thousands of marine species, including sea otters, sea urchins, and various fish.
    
    In recent years, rising ocean temperatures and the decline of sea otter populations have led to an explosion in the sea urchin population. Urchins graze aggressively on kelp holdfasts, destroying entire forest canopies in a phenomenon known as 'urchin barrens'.
    
    Questions 1-3
    Choose the correct letter, A, B, C or D.
    
    1. Giant kelp can grow at an astonishing rate of up to 60 cm per day when
    A) Sea otters are completely absent
    B) Water is cold, nutrient-rich, and sunny
    C) Sea urchins graze on holdfasts
    D) Ocean temperatures rise above normal
    
    2. What primary danger threatens the survival of kelp forests today?
    A) Overfishing of large sharks
    B) Rapid growth of marine plants
    C) Proliferation of aggressive sea urchins due to rising temperatures
    D) Extreme cold water currents
    
    Questions 4-5
    Complete the sentences below. Choose NO MORE THAN TWO WORDS from the passage.
    
    4. Kelp forests that have been completely devastated by grazing urchins are referred to as _____.
    
    5. Sea otters play a crucial role in kelp ecosystems by keeping the population of _____ under control.
    
    Answers:
    1. B
    2. C
    3. urchin barrens
    4. sea urchins
    """
    
    prompt = f"""
Siz ingliz tili bo'yicha professional imtihon tuzuvchisiz (IELTS, CEFR, Cambridge).
Quyidagi matndan BARCHA test savollarini ajratib oling va JSON formatida qaytaring.

O'TA MUHIM QOIDALAR (TO'LIQLIK VA MATN SHARTI):
1. **Shart va matnni saqlash:** Agar savol biror matnga (Reading passage), umumiy ko'rsatmaga (Instructions, masalan: "Choose NO MORE THAN TWO WORDS"), jadvalga yoki dialogga tegishli bo'lsa, USHBU KO'RSATMA VA MATNNI SAVOL TEXTIGA TO'LIQ KIRITING! O'quvchi savolga qarab qaysi matndan javob topishini va topshiriq shartini to'liq ko'rishi shart.
   Format:
   "text": "📖 [Matn/Ko'rsatma]: ...\\n\\n❓ [Savol]: ..." (yoki savolning o'zi va to'liq sharti).
2. **Hech bir savolni tashlab ketmang:** Matndagi barcha raqamlangan savollarni (1, 2, 3, 4, 5...) to'liq oling.
3. **Savol turlari ("type"):**
   - "mcq" — Variantli savollar. "options" massivida barcha variantlar (A, B, C, D) bo'lsin.
   - "true_false" — To'g'ri/Noto'g'ri savollar. "options": ["True", "False"].
   - "fill_blank" — Bo'sh joyni to'ldirish (`____`). "options": [].
   - "short_answer" — Ochiq yozma savollar. "options": [].
4. **To'g'ri javob:** Matndagi Answer Key yoki matn mantiqidan kelib chiqib "correct_answer" maydoniga aniq to'g'ri javobni yozing.

JSON sxemasi:
[
  {{
    "order_num": 1,
    "type": "mcq" | "true_false" | "fill_blank" | "short_answer",
    "text": "Savolning to'liq matni (kerak bo'lsa o'qish matni/ko'rsatmasi bilan birga)",
    "options": ["A) ...", "B) ..."] yoki ["True", "False"] yoki [],
    "correct_answer": "...",
    "needs_review": false
  }}
]

Faqat toza JSON array qaytaring.

Matn:
{sample_pdf_text}
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
            parsed = json.loads(out)
            print(f"Total extracted: {len(parsed)}")
            for q in parsed:
                print("\n===============================")
                print(f"Savol #{q['order_num']} ({q['type']}):")
                print(f"Text:\n{q['text']}")
                print(f"Options: {q['options']}")
                print(f"Correct: {q['correct_answer']}")

if __name__ == "__main__":
    asyncio.run(test_full_context_prompt())
