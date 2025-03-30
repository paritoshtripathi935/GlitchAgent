from pymongo import MongoClient
from src.constants import MONGO_URI
from functools import lru_cache
import logging


@lru_cache(maxsize=1)
def get_mongo_instance():
    """
    Get MongoDB connection with LRU caching
    :return: MongoDB connection
    """
    client = MongoClient(MONGO_URI)
    db = client["glitch_agent"]
    return db
