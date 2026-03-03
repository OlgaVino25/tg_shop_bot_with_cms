from environs import Env


env = Env()
env.read_env()

TG_TOKEN = env.str("TG_TOKEN")
ADMIN_CHAT_ID = env.str("ADMIN_CHAT_ID")

REDIS_HOST = env.str("REDIS_HOST", "localhost")
REDIS_PORT = env.int("REDIS_PORT", 6379)
REDIS_DB = env.int("REDIS_DB", 0)
