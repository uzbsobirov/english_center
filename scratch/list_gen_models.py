import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

async def list_models():
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            for m in data.get("models", []):
                if "generateContent" in m.get("supportedGenerationMethods", []):
                    print(m.get("name"))

if __name__ == "__main__":
    asyncio.run(list_models())
