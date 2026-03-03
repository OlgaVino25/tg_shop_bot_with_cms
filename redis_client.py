import redis
from settings import REDIS_HOST, REDIS_PORT, REDIS_DB


r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
)



