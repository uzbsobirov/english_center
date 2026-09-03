import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

async def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"Key found: {bool(api_key)}, length: {len(api_key) if api_key else 0}")
    
    # Try gemini-1.5-flash endpoint and gemini-2.0-flash endpoint
    models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    
    async with aiohttp.ClientSession() as session:
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": "Hello, respond with JSON: {\"status\": \"ok\", \"message\": \"Gemini is active!\"}"}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            try:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    status = resp.status
                    text = await resp.text()
                    print(f"Model {model} -> HTTP {status}")
                    if status == 200:
                        print("✅ Success response:", text)
                        return True
                    else:
                        print(f"❌ Error: {text}")
            except Exception as e:
                print(f"⚠️ Request exception for {model}: {e}")
                
    return False

if __name__ == "__main__":
    asyncio.run(test_gemini())
