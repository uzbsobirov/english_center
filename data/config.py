import os
from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")
ADMINS = env.list("ADMINS")
IP = env.str("ip", "127.0.0.1")
WEBAPP_URL = env.str("WEBAPP_URL", "http://localhost:5173")
DEV_MODE = env.bool("DEV_MODE", True)


def get_webapp_url() -> str:
    """Hozirgi faol WebApp havolasini .env dan dinamik qaytaradi."""
    try:
        env.read_env(override=True)
        return env.str("WEBAPP_URL", "http://localhost:5173")
    except Exception:
        return os.getenv("WEBAPP_URL", WEBAPP_URL)