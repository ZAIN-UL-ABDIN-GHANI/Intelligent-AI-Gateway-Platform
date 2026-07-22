"""Admin endpoints: org bootstrap, API keys, budget/policy (Phase 6 §7-10).

Org creation + JWT login are simplified for the hackathon demo (no password
flow) -- a real deployment would add proper user auth (Phase 2 out of MVP
scope: SSO). Here, creating an org directly issues an admin token so the
dashboard can be exercised end-to-end.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import create_access_token, generate_api_key, hash_api_key
from app.db import crud
from app.deps import get_db_session, require_admin_session

router = APIRouter(prefix="/v1/admin", tags=["admin"])


class CreateOrgRequest(BaseModel):
    name: str
    privacy_policy: str = "strict"


class CreateApiKeyRequest(BaseModel):
    label: str = ""


class UpdateBudgetRequest(BaseModel):
    monthly_limit: float


@router.post("/organizations", status_code=201)
def create_organization(body: CreateOrgRequest, db: Session = Depends(get_db_session)):
    org = crud.create_organization(db, body.name, body.privacy_policy)
    token = create_access_token(org.id)
    return {"org_id": org.id, "name": org.name, "admin_token": token}


@router.post("/api-keys", status_code=201)
def create_api_key(
    body: CreateApiKeyRequest,
    session=Depends(require_admin_session),
    db: Session = Depends(get_db_session),
):
    raw_key = generate_api_key()
    key = crud.create_api_key(db, org_id=session["org_id"], key_hash=hash_api_key(raw_key), label=body.label)
    return {"key": raw_key, "key_id": key.id, "note": "store this key now -- it will not be shown again"}


@router.put("/budget")
def update_budget(
    body: UpdateBudgetRequest,
    session=Depends(require_admin_session),
    db: Session = Depends(get_db_session),
):
    budget = crud.get_budget(db, session["org_id"])
    if budget is None:
        raise HTTPException(404, "No budget record found for org")
    budget.monthly_limit = body.monthly_limit
    db.commit()
    return {"status": "updated", "monthly_limit": float(budget.monthly_limit)}
