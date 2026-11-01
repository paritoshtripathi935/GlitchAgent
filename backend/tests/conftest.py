import os
import sys

import fakeredis
import fastapi
import mongomock
import pytest

# test_glitch_agent.py is a live-server demo (needs localhost:8000 + pytest-asyncio); opt in with RUN_LIVE_TESTS=1
collect_ignore = [] if os.getenv("RUN_LIVE_TESTS") else ["test_glitch_agent.py"]

# Env must be set before the app is imported (constants validate at import).
os.environ.setdefault("MONGO_URI", "mongodb://x")
os.environ.setdefault("REDIS_URI", "redis://x")
os.environ.pop("CLERK_JWT_ISSUER", None)
os.environ.pop("CLOUDFLARE_API_KEY", None)
os.environ.pop("CLOUDFLARE_ACCOUNT_ID", None)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Newer FastAPI rejects these legacy kwargs if any are still passed.
_orig_init = fastapi.FastAPI.__init__


def _init(self, *a, **k):
    k.pop("openapi_prefix", None)
    k.pop("api_prefix", None)
    _orig_init(self, *a, **k)


fastapi.FastAPI.__init__ = _init

import src.database.connectors.mongo_connector as mc  # noqa: E402
import src.database.connectors.redis_connector as rc  # noqa: E402

_db = mongomock.MongoClient()["t"]
mc.get_mongo_instance = lambda: _db
rc.get_redis_client = lambda: fakeredis.FakeRedis()

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from src.routers.v1 import glitch_agent as router  # noqa: E402


@pytest.fixture
def db():
    for name in _db.list_collection_names():
        _db.drop_collection(name)
    router.execution_results.clear()
    return _db


@pytest.fixture
def client(db):
    return TestClient(main.app)
