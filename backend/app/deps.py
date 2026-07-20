"""Shared FastAPI dependencies: DB session + API key / JWT auth."""
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.rate_limit import check_rate_limit
from app.core.security import decode_access_token, hash_api_key
from app.db import crud
from app.db.models import ApiKey
from app.db.session import get_db


def get_db_session():
    yield from get_db()


def require_api_key(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db_session),
) -> ApiKey:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or malformed Authorization header")
    raw_key = authorization.removeprefix("Bearer ").strip()
    key_hash = hash_api_key(raw_key)
    api_key = crud.get_org_by_api_key_hash(db, key_hash)
    if api_key is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
    if not check_rate_limit(api_key.id):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded")
    return api_key


def require_admin_session(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or malformed Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return decode_access_token(token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session token") from exc
