import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

async def test_call():
    api_key = os.getenv("GEMINI_API_KEY")
    candidates = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-3.5-flash"]
    
    async with aiohttp.ClientSession() as session:
        for c in candidates:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{c}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": "Return JSON list with 1 question: [{\"order_num\": 1, \"type\": \"mcq\", \"text\": \"Sample?\", \"options\": [\"A) 1\", \"B) 2\"], \"correct_answer\": \"A) 1\"}]"}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            async with session.post(url, json=payload) as resp:
                print(f"Candidate '{c}' -> status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    txt = data["candidates"][0]["content"]["parts"][0]["text"]
                    print("SUCCESS Output:", txt)
                    return c
                else:
                    err_txt = await resp.text()
                    print(f"Error for {c}: {err_txt[:150]}")
    return None

if __name__ == "__main__":
    asyncio.run(test_call())
