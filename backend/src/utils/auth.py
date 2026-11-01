"""Clerk JWT auth. Mirrors MiniHarvery: RS256 session tokens verified against
`{CLERK_JWT_ISSUER}/.well-known/jwks.json`, JWKS cached in-process.

If CLERK_JWT_ISSUER is unset, auth is disabled and every caller is "local".
"""
import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

import httpx
from fastapi import Header, HTTPException
from jose import jwt
from jose.exceptions import JWTError

LOCAL_USER = "local"
_jwks_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}


class ClerkAuthError(Exception):
    pass


def _issuer() -> str:
    return os.getenv("CLERK_JWT_ISSUER", "").strip()


def warn_if_auth_disabled() -> None:
    """Call once at startup."""
    if not _issuer():
        logging.warning("CLERK_JWT_ISSUER is not set: auth DISABLED, all requests run as user 'local'")


def _fetch_jwks(issuer: str) -> Dict[str, Any]:
    cached = _jwks_cache.get(issuer)
    if cached and cached[0] > time.time():
        return cached[1]
    url = issuer.rstrip("/") + "/.well-known/jwks.json"
    try:
        resp = httpx.get(url, timeout=5.0)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise ClerkAuthError(f"Could not fetch JWKS from {url}: {exc}") from exc
    jwks = resp.json()
    ttl = int(os.getenv("CLERK_JWKS_TTL_SECONDS", "3600"))
    _jwks_cache[issuer] = (time.time() + ttl, jwks)
    return jwks


def _key_for_kid(jwks: Dict[str, Any], kid: str) -> Optional[Dict[str, Any]]:
    return next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)


def verify_clerk_jwt(token: str) -> Dict[str, Any]:
    issuer = _issuer()
    if not issuer:
        raise ClerkAuthError("CLERK_JWT_ISSUER not configured")
    try:
        kid = jwt.get_unverified_header(token).get("kid")
    except JWTError as exc:
        raise ClerkAuthError(f"Malformed token: {exc}") from exc
    if not kid:
        raise ClerkAuthError("Token header missing kid")

    key = _key_for_kid(_fetch_jwks(issuer), kid)
    if key is None:  # key may have rotated: refresh once
        _jwks_cache.pop(issuer, None)
        key = _key_for_kid(_fetch_jwks(issuer), kid)
        if key is None:
            raise ClerkAuthError(f"No JWKS key for kid={kid}")
    try:
        claims = jwt.decode(token, key, algorithms=["RS256"], issuer=issuer, options={"verify_aud": False})
    except JWTError as exc:
        raise ClerkAuthError(f"Token verification failed: {exc}") from exc
    if not claims.get("sub"):
        raise ClerkAuthError("Token missing sub claim")
    return claims


def get_user_id(authorization: Optional[str] = Header(None)) -> str:
    """FastAPI dependency: returns the Clerk `sub`, or "local" when auth is disabled.
    Sync on purpose: the JWKS fetch blocks, so FastAPI runs it in the threadpool."""
    if not _issuer():
        return LOCAL_USER
    if not authorization or not authorization.startswith("Bearer ") or not authorization[7:].strip():
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    try:
        return verify_clerk_jwt(authorization[7:].strip())["sub"]
    except ClerkAuthError as exc:
        logging.info("Rejected invalid Clerk token: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid Clerk token") from exc
