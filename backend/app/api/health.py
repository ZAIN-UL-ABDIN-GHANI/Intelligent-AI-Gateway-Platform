"""GET /v1/health and /v1/metrics (Phase 6 §11-12)."""
from fastapi import APIRouter, Response

from app.providers.litellm_client import get_provider_status
from app.routing.health import health_snapshot

router = APIRouter(tags=["health"])


@router.get("/v1/health")
def health():
    backends = health_snapshot()
    providers = get_provider_status()
    combined = {}
    for name, status in backends.items():
        combined[name] = {
            "status": status,
            "mode": providers[name]["mode"],
            "model": providers[name]["model"],
            "provider": providers[name]["provider"],
        }
    return {"status": "ok", "backends": combined}


@router.get("/v1/metrics")
def metrics():
    snapshot = health_snapshot()
    providers = get_provider_status()
    lines = [
        "# HELP ai_gateway_backend_health 1 if healthy, 0 if degraded",
        "# TYPE ai_gateway_backend_health gauge",
    ]
    for name, status in snapshot.items():
        mode = providers[name]["mode"]
        lines.append(
            f'ai_gateway_backend_health{{backend="{name}",mode="{mode}"}} '
            f'{1 if status == "healthy" else 0}'
        )
    return Response(content="\n".join(lines) + "\n", media_type="text/plain")
