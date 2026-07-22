"""Analytics endpoints (Phase 6 §4-6)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import crud
from app.deps import get_db_session, require_api_key

router = APIRouter(prefix="/v1/analytics", tags=["analytics"])


class CostEntry(BaseModel):
    backend: str
    cost: float


class CostResponse(BaseModel):
    total_cost: float
    breakdown: list[CostEntry]


class DistributionEntry(BaseModel):
    backend: str
    count: int
    share: float


class DistributionResponse(BaseModel):
    distribution: list[DistributionEntry]


class BudgetResponse(BaseModel):
    monthly_limit: float
    current_spend: float
    pressure: float


@router.get("/cost", response_model=CostResponse)
def cost_analytics(api_key=Depends(require_api_key), db: Session = Depends(get_db_session)):
    total, breakdown = crud.cost_breakdown(db, api_key.org_id)
    return CostResponse(
        total_cost=round(total, 6),
        breakdown=[CostEntry(backend=k, cost=round(v, 6)) for k, v in breakdown.items()],
    )


@router.get("/routing-distribution", response_model=DistributionResponse)
def routing_distribution(api_key=Depends(require_api_key), db: Session = Depends(get_db_session)):
    dist = crud.routing_distribution(db, api_key.org_id)
    total = sum(dist.values()) or 1
    return DistributionResponse(
        distribution=[
            DistributionEntry(backend=k, count=v, share=round(v / total, 4)) for k, v in dist.items()
        ]
    )


@router.get("/budget", response_model=BudgetResponse)
def budget_status(api_key=Depends(require_api_key), db: Session = Depends(get_db_session)):
    budget = crud.get_budget(db, api_key.org_id)
    if budget is None:
        return BudgetResponse(monthly_limit=0, current_spend=0, pressure=0)
    limit = float(budget.monthly_limit)
    spend = float(budget.current_spend)
    return BudgetResponse(
        monthly_limit=limit,
        current_spend=spend,
        pressure=round(spend / limit, 4) if limit else 0,
    )
