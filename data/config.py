from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")
ADMINS = env.list("ADMINS")
IP = env.str("ip", "127.0.0.1")
WEBAPP_URL = env.str("WEBAPP_URL", "http://localhost:5173")
DEV_MODE = env.bool("DEV_MODE", True)