from dotenv import load_dotenv
import os
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
REDIS_URI = os.getenv("REDIS_URI")


if not MONGO_URI:
    raise ValueError("No MONGO_URI set for MongoDB")
if not REDIS_URI:
    raise ValueError("No REDIS_URI set for Redis")