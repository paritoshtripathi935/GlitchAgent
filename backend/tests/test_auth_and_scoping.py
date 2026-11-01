import time
from datetime import datetime

import pytest
from jose import jwt
from jose.backends.cryptography_backend import CryptographyRSAKey
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

import src.utils.auth as auth
from src.models.glitch_agent import CommandResponse, BrowserAction
from src.routers.v1 import glitch_agent as router

ISSUER = "https://clerk.test"
BASE = "/v1/glitch-agent"

_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_pem = _priv.private_bytes(
    serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
).decode()
_jwk = {**CryptographyRSAKey(_priv.public_key(), "RS256").to_dict(), "kid": "k1", "use": "sig"}
_jwk = {k: (v.decode() if isinstance(v, bytes) else v) for k, v in _jwk.items()}


def token(sub, iss=ISSUER, exp_in=300, kid="k1"):
    return jwt.encode({"sub": sub, "iss": iss, "exp": int(time.time()) + exp_in}, _pem, "RS256", headers={"kid": kid})


def hdr(sub, **kw):
    return {"Authorization": f"Bearer {token(sub, **kw)}"}


@pytest.fixture
def clerk(monkeypatch):
    monkeypatch.setenv("CLERK_JWT_ISSUER", ISSUER)
    auth._jwks_cache.clear()
    monkeypatch.setattr(auth, "_fetch_jwks", lambda issuer: {"keys": [_jwk]})


class FakeService:
    async def translate_command(self, request):
        return CommandResponse(request_id=f"r-{request.command}", actions=[BrowserAction(action="screenshot")])

    async def stop_browser(self):
        pass


@pytest.fixture
def fake_service(monkeypatch):
    svc = FakeService()
    monkeypatch.setattr(router, "get_browser_automation_service", lambda: svc)
    # don't run the browser in the background task
    monkeypatch.setattr(router, "execute_actions_background", _noop)
    return svc


async def _noop(*a, **k):
    return None


def test_auth_disabled_works(client, fake_service):
    r = client.post(f"{BASE}/command", json={"command": "x"})
    assert r.status_code == 200
    assert client.get(f"{BASE}/history").json()[0]["request_id"] == "r-x"
    assert client.get("/health").status_code == 200


def test_missing_and_invalid_token_401(client, clerk, fake_service):
    assert client.get(f"{BASE}/history").status_code == 401
    assert client.get(f"{BASE}/history", headers={"Authorization": "Bearer junk"}).status_code == 401
    assert client.get(f"{BASE}/history", headers=hdr("a", iss="https://evil")).status_code == 401
    assert client.get(f"{BASE}/history", headers=hdr("a", exp_in=-10)).status_code == 401
    assert client.post(f"{BASE}/stop-browser").status_code == 401
    assert client.get("/health").status_code == 200  # health stays public


def test_valid_token_ok(client, clerk, fake_service):
    assert client.get(f"{BASE}/history", headers=hdr("user_a")).status_code == 200
    assert client.post(f"{BASE}/stop-browser", headers=hdr("user_a")).status_code == 200


def test_user_isolation(client, clerk, fake_service, db):
    a, b = hdr("user_a"), hdr("user_b")
    assert client.post(f"{BASE}/command", json={"command": "a1"}, headers=a).status_code == 200
    assert db.command_executions.find_one({"request_id": "r-a1"})["user_id"] == "user_a"
    assert [h["request_id"] for h in client.get(f"{BASE}/history", headers=a).json()] == ["r-a1"]
    assert client.get(f"{BASE}/history", headers=b).json() == []
    assert client.get(f"{BASE}/execution/r-a1", headers=a).status_code == 200
    assert client.get(f"{BASE}/execution/r-a1", headers=b).status_code == 404

    # in-memory result is owner-checked too
    from src.models.glitch_agent import ExecutionResult
    router.execution_results["mem"] = ("user_a", ExecutionResult(request_id="mem", success=True, message="ok"))
    assert client.get(f"{BASE}/execution/mem", headers=a).status_code == 200
    assert client.get(f"{BASE}/execution/mem", headers=b).status_code == 404


def test_command_503_without_cloudflare_creds(client, monkeypatch):
    monkeypatch.setattr(router, "_service_instance", None)
    r = client.post(f"{BASE}/command", json={"command": "x"})
    assert r.status_code == 503
