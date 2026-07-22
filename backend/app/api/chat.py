"""POST /v1/chat/completions (Phase 6 §1)."""
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.cache.exact_cache import get_cached, set_cached
from app.cache.semantic_cache import semantic_lookup, semantic_store
from app.db import crud
from app.deps import get_db_session, require_api_key
from app.providers.litellm_client import ProviderError, call_backend_stream
from app.routing.graph import run_routing
from app.routing.health import mark_degraded
from app.schemas.chat import ChatCompletionRequest, ChatCompletionResponse, Usage

router = APIRouter(prefix="/v1", tags=["chat"])


def _sse_stream(backend_name: str, messages: list[dict]):
    """Yield Server-Sent Events for streaming responses."""
    try:
        for chunk in call_backend_stream(backend_name, messages):
            payload = json.dumps({"content": chunk, "routed_model": backend_name})
            yield f"data: {payload}\n\n"
        yield "data: [DONE]\n\n"
    except ProviderError as exc:
        error_payload = json.dumps({"error": str(exc), "error_type": exc.error_type})
        yield f"data: {error_payload}\n\n"


@router.post("/chat/completions", response_model=ChatCompletionResponse)
def chat_completions(
    body: ChatCompletionRequest,
    api_key=Depends(require_api_key),
    db: Session = Depends(get_db_session),
):
    org = api_key.organization
    prompt = body.messages[-1].content
    messages = [m.model_dump() for m in body.messages]

    cached = get_cached(org.id, prompt)
    if cached is None:
        from app.routing.agents.risk import classify_risk
        risk_level = classify_risk(prompt)
        cached = semantic_lookup(org.id, prompt, risk_level)

    if cached is not None:
        if body.stream:
            # Stream cached content as a single SSE chunk
            def _cached_stream():
                payload = json.dumps({"content": cached["content"], "routed_model": cached["routed_model"]})
                yield f"data: {payload}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(_cached_stream(), media_type="text/event-stream")

        trace = crud.record_trace(
            db,
            org_id=org.id,
            api_key_id=api_key.id,
            backend_name=cached["routed_model"],
            intent=cached.get("intent", "unknown"),
            complexity_score=0.0,
            risk_level="none",
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
            latency_ms=0,
            cache_hit=True,
            reason="served from cache",
        )
        return ChatCompletionResponse(
            id=trace.id,
            trace_id=trace.id,
            routed_model=cached["routed_model"],
            content=cached["content"],
            usage=Usage(input_tokens=0, output_tokens=0, cost=0.0),
            cache_hit=True,
        )

    budget = crud.get_budget(db, org.id)
    result = run_routing(
        prompt=prompt,
        messages=messages,
        org_id=org.id,
        privacy_policy=org.privacy_policy,
        current_spend=float(budget.current_spend) if budget else 0.0,
        monthly_limit=float(budget.monthly_limit) if budget else 100.0,
        force_backend=body.force_backend if body.model == "auto" else (None if body.model == "auto" else body.model),
    )

    if result.get("error") or not result.get("content"):
        for attempted in result.get("attempted_backends", []):
            mark_degraded(attempted)
        raise HTTPException(503, detail={"code": "all_backends_unavailable", "message": "No backend could serve this request"})

    # If stream was requested, re-stream from the chosen backend
    if body.stream:
        return StreamingResponse(
            _sse_stream(result["chosen_backend"], messages),
            media_type="text/event-stream",
        )

    trace = crud.record_trace(
        db,
        org_id=org.id,
        api_key_id=api_key.id,
        backend_name=result["chosen_backend"],
        intent=result["intent"],
        complexity_score=result["complexity"],
        risk_level=result["risk_level"],
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
        cost=result.get("actual_cost", 0.0),
        latency_ms=int(result.get("latency_ms", 0)),
        cache_hit=False,
        reason=result["reason"],
        candidate_scores=result.get("candidate_scores"),
    )

    response_payload = {
        "routed_model": result["chosen_backend"],
        "content": result["content"],
        "intent": result["intent"],
    }
    set_cached(org.id, prompt, response_payload)
    semantic_store(org.id, prompt, response_payload, result["risk_level"])

    return ChatCompletionResponse(
        id=trace.id,
        trace_id=trace.id,
        routed_model=result["chosen_backend"],
        content=result["content"],
        usage=Usage(
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            cost=float(result.get("actual_cost", 0.0)),
        ),
        cache_hit=False,
    )
