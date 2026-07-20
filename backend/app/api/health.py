"""GET /v1/health and /v1/metrics (Phase 6 §11-12)."""
from fastapi import APIRouter, Response

from app.routing.health import health_snapshot

router = APIRouter(tags=["health"])

_request_count = {"total": 0}


@router.get("/v1/health")
def health():
    return {"status": "ok", "backends": health_snapshot()}


@router.get("/v1/metrics")
def metrics():
    snapshot = health_snapshot()
    lines = [
        "# HELP ai_gateway_backend_health 1 if healthy, 0 if degraded",
        "# TYPE ai_gateway_backend_health gauge",
    ]
    for name, status in snapshot.items():
        lines.append(f'ai_gateway_backend_health{{backend="{name}"}} {1 if status == "healthy" else 0}')
    return Response(content="\n".join(lines) + "\n", media_type="text/plain")
