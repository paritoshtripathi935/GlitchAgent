import redis
from src.constants import REDIS_URI
from functools import lru_cache


@lru_cache(maxsize=1)
def get_redis_client():
    """
    Get Redis connection with LRU caching
    :return: Redis connection
    """
    redis_client = redis.Redis.from_url(REDIS_URI)  
    return redis_client
