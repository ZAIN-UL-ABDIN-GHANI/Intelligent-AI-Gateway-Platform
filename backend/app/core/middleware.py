"""Production middleware: request IDs, timing, security headers, error handling."""
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("ai_gateway.middleware")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error("Unhandled error [%s] %s %s: %s", request_id, request.method, request.url.path, exc)
            return JSONResponse(
                status_code=500,
                content={"error": "internal_server_error", "message": "An unexpected error occurred", "request_id": request_id},
            )

        latency_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{latency_ms:.1f}"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        logger.info(
            "%s %s %d %.1fms [%s]",
            request.method, request.url.path, response.status_code, latency_ms, request_id,
        )
        return response


def register_middleware(app: FastAPI) -> None:
    app.add_middleware(RequestContextMiddleware)
