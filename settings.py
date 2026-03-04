from environs import Env


env = Env()
env.read_env()

TG_TOKEN = env.str("TG_TOKEN")
ADMIN_CHAT_ID = env.str("ADMIN_CHAT_ID")

