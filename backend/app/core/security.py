"""API key hashing + JWT helpers (Phase 6 §13)."""
import hashlib
import secrets
import time

import jwt

from app.config import get_settings

_JWT_EXPIRY_SECONDS = 60 * 60 * 24 * 7  # 7 days


def generate_api_key() -> str:
    return f"agw_{secrets.token_urlsafe(32)}"


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def create_access_token(org_id: str, role: str = "org_admin") -> str:
    settings = get_settings()
    payload = {
        "org_id": org_id,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + _JWT_EXPIRY_SECONDS,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
