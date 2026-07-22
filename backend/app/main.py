"""FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, analytics, chat, health, traces
from app.core.logging import setup_logging
from app.core.middleware import register_middleware
from app.config import get_settings
from app.db.session import init_db

settings = get_settings()
setup_logging()

app = FastAPI(
    title=settings.app_name,
    description="Enterprise AI Gateway -- Hybrid Token-Efficient Routing Agent",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_middleware(app)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(traces.router)
app.include_router(analytics.router)
app.include_router(admin.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"service": settings.app_name, "status": "running", "docs": "/docs"}
