# Phase 12 — Deployment
## Enterprise AI Gateway: Hybrid Token-Efficient Routing Agent

This phase is implemented — see the repo root for the actual files referenced below.

---

## 1. Dockerfiles
- `backend/Dockerfile` — `python:3.12-slim`, installs `requirements.txt`, runs `uvicorn app.main:app` on port 8000.
- `frontend/Dockerfile` — multi-stage: `node:20-slim` build stage produces the Vite production bundle, served by `nginx:alpine` on port 80 (mapped to 5173 externally).

## 2. docker-compose.yml
Orchestrates 5 services: `postgres`, `redis`, `ollama` (local Gemma), `backend`, `frontend`, with health checks gating backend startup on Postgres/Redis readiness. One command (`docker compose up --build`) brings up the full stack — this was the explicit design goal from Phase 1 constraints (judge-machine deployability).

## 3. Environment Variables
Documented in `.env.example` at repo root: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `GEMMA_BASE_URL`, `GEMMA_MODEL_NAME`. Any blank provider key runs that provider in mock mode (see `app/providers/litellm_client.py`) rather than failing — this was a deliberate NFR-7 (graceful degradation) decision so the system demos fully without live credentials.

## 4. CI/CD Pipeline
`.github/workflows/ci.yml` — three jobs on every push/PR to `main`:
1. `backend-tests` — installs backend deps, runs the full pytest suite with coverage.
2. `frontend-build` — installs frontend deps, runs `npm run build` (TypeScript check + Vite bundle).
3. `docker-build` — builds both Docker images, gated on the two test jobs passing.

## 5. Production Deployment Guide
For a real (non-demo) deployment beyond the hackathon:
- Replace `create_all()` in `app/db/session.py` with Alembic migrations (scaffold documented in Phase 5 §7) run as a release-gate CI step.
- Put a real reverse proxy (nginx/Envoy/Kong) in front of the FastAPI gateway for TLS termination and request-size limits.
- Move secrets from `.env` to a proper secret manager (AWS Secrets Manager / Vault / Docker Swarm secrets) — the app already reads all config from environment variables, so this is a deployment-only change.
- Run multiple `backend` replicas behind a load balancer; the app is stateless by design (all shared state in Postgres/Redis), so this requires no code change.
- Point `GEMMA_BASE_URL` at a dedicated, appropriately-resourced Ollama (or vLLM) deployment rather than a co-located container.

## 6. Monitoring
`GET /v1/metrics` exposes Prometheus-format backend health gauges today; extending it to request-count/latency histograms is a small addition to `app/api/health.py` using `prometheus-client`, left as a documented next step rather than built, to keep the MVP lean.

## 7. Logging
`app/core/logging.py` configures structured JSON logging to stdout — container-log-aggregator friendly (CloudWatch, Loki, Datadog, etc.) out of the box, no code change needed for most log pipelines.

## 8. Backup Strategy
Postgres: standard `pg_dump` on a schedule, or managed-Postgres automated backups if deployed on RDS/Cloud SQL — no gateway-specific state lives outside Postgres except the semantic-cache FAISS index and Redis cache/stats, both of which are safely rebuildable/lossy-tolerant (cache misses degrade to normal routing, not failure; confidence-table loss reverts to documented cold-start priors).

---

**Next:** Phase 13 — Documentation (this docs folder + README, already complete).
