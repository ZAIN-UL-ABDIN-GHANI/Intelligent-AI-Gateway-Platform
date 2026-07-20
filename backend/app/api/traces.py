"""GET /v1/traces/{id} and POST /v1/feedback (Phase 6 §2-3)."""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import crud
from app.deps import get_db_session, require_api_key
from app.schemas.chat import FeedbackRequest
from app.routing.agents.confidence import update_confidence

router = APIRouter(prefix="/v1", tags=["traces"])


@router.get("/traces/{trace_id}")
def get_trace(trace_id: str, api_key=Depends(require_api_key), db: Session = Depends(get_db_session)):
    trace = crud.get_trace(db, trace_id)
    if trace is None:
        raise HTTPException(404, detail={"code": "trace_not_found", "message": "No such trace"})
    if trace.org_id != api_key.org_id:
        raise HTTPException(403, detail={"code": "forbidden", "message": "Trace belongs to a different org"})

    return {
        "trace_id": trace.id,
        "intent": trace.intent,
        "complexity_score": trace.complexity_score,
        "risk_level": trace.risk_level,
        "candidate_scores": json.loads(trace.candidate_scores) if trace.candidate_scores else {},
        "chosen_backend": trace.backend_name,
        "reason": trace.reason,
        "cost": float(trace.cost or 0),
        "latency_ms": trace.latency_ms,
        "cache_hit": trace.cache_hit,
        "created_at": trace.created_at.isoformat(),
    }


@router.post("/feedback", status_code=201)
def submit_feedback(body: FeedbackRequest, api_key=Depends(require_api_key), db: Session = Depends(get_db_session)):
    trace = crud.get_trace(db, body.trace_id)
    if trace is None:
        raise HTTPException(404, detail={"code": "trace_not_found", "message": "No such trace"})
    fb = crud.create_feedback(db, body.trace_id, body.rating, body.comment)
    if trace.intent and trace.backend_name:
        update_confidence(trace.intent, trace.backend_name, success=(body.rating == "up"))
    return {"id": fb.id, "status": "recorded"}
