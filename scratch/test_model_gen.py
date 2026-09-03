import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

async def test_generation():
    api_key = os.getenv("GEMINI_API_KEY")
    # Test models
    models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    
    async with aiohttp.ClientSession() as session:
        for m in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": "Write 1 test question in JSON format: [{\"text\": \"Q\", \"type\": \"mcq\"}]"}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            async with session.post(url, json=payload) as resp:
                print(f"Model {m} status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    out = data["candidates"][0]["content"]["parts"][0]["text"]
                    print("Generated output:", out[:200])
                    return m
    return None

if __name__ == "__main__":
    res = asyncio.run(test_generation())
    print("Best working model:", res)
