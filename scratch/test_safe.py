import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

async def test():
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.text()
            print("Status:", resp.status)
            print("Response:", data[:400])

if __name__ == "__main__":
    asyncio.run(test())
