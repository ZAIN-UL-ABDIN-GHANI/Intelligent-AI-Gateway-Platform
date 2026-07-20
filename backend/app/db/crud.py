"""Simple CRUD helpers used by API routes."""
import json
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.db import models


def get_org_by_api_key_hash(db: Session, key_hash: str) -> Optional[models.ApiKey]:
    return (
        db.query(models.ApiKey)
        .filter(models.ApiKey.key_hash == key_hash, models.ApiKey.active.is_(True))
        .first()
    )


def create_organization(db: Session, name: str, privacy_policy: str = "strict") -> models.Organization:
    org = models.Organization(name=name, privacy_policy=privacy_policy)
    db.add(org)
    db.commit()
    db.refresh(org)
    budget = models.Budget(org_id=org.id, monthly_limit=100.0, current_spend=0.0)
    db.add(budget)
    db.commit()
    return org


def create_api_key(db: Session, org_id: str, key_hash: str, label: str = "") -> models.ApiKey:
    key = models.ApiKey(org_id=org_id, key_hash=key_hash, label=label)
    db.add(key)
    db.commit()
    db.refresh(key)
    return key


def record_trace(db: Session, **kwargs) -> models.RoutingTrace:
    candidate_scores = kwargs.pop("candidate_scores", None)
    trace = models.RoutingTrace(
        candidate_scores=json.dumps(candidate_scores) if candidate_scores else None,
        **kwargs,
    )
    db.add(trace)
    db.commit()
    db.refresh(trace)

    # update budget spend
    budget = db.query(models.Budget).filter(models.Budget.org_id == kwargs["org_id"]).first()
    if budget is not None and trace.cost:
        budget.current_spend = Decimal(str(budget.current_spend)) + Decimal(str(trace.cost))
        db.commit()

    return trace


def get_trace(db: Session, trace_id: str) -> Optional[models.RoutingTrace]:
    return db.query(models.RoutingTrace).filter(models.RoutingTrace.id == trace_id).first()


def create_feedback(db: Session, trace_id: str, rating: str, comment: Optional[str]) -> models.Feedback:
    fb = models.Feedback(trace_id=trace_id, rating=rating, comment=comment)
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb


def get_budget(db: Session, org_id: str) -> Optional[models.Budget]:
    return db.query(models.Budget).filter(models.Budget.org_id == org_id).first()


def cost_breakdown(db: Session, org_id: str):
    traces = db.query(models.RoutingTrace).filter(models.RoutingTrace.org_id == org_id).all()
    breakdown: dict[str, float] = {}
    total = 0.0
    for t in traces:
        c = float(t.cost or 0)
        breakdown[t.backend_name] = breakdown.get(t.backend_name, 0.0) + c
        total += c
    return total, breakdown


def routing_distribution(db: Session, org_id: str):
    traces = db.query(models.RoutingTrace).filter(models.RoutingTrace.org_id == org_id).all()
    dist: dict[str, int] = {}
    for t in traces:
        dist[t.backend_name] = dist.get(t.backend_name, 0) + 1
    return dist
