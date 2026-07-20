# AI Gateway — Hybrid Token-Efficient Routing Agent

An enterprise AI gateway that intelligently routes chat requests across a **local Gemma model** and the **Claude, GPT, and Gemini** APIs — balancing quality, cost, latency, and privacy per request, with full explainability.

Built for the *Hybrid Token-Efficient Routing Agent* hackathon track. Full design docs for all 13 engineering phases are in [`docs/`](./docs).

---

## What it actually does

1. A request comes in via an OpenAI-compatible `/v1/chat/completions` endpoint.
2. A LangGraph pipeline scores it for **intent**, **complexity**, **PII/risk**, and **predicted tokens**.
3. A weighted policy picks the best eligible backend (quality confidence, cost, latency, budget pressure) — PII-flagged content is automatically restricted to the local model.
4. The response comes back with a `trace_id`; `/v1/traces/{id}` explains exactly why that backend was chosen.
5. Cost/token/routing-distribution analytics and a live "routing manifest" are visible in the dashboard.

Backends without a configured API key run in **mock mode** automatically, so the whole system — routing, caching, analytics — is fully demoable with zero live API keys and zero cost.

---

## Quickstart (Docker Compose)

```bash
cp .env.example .env        # optionally fill in API keys; blank = mock mode
docker compose up --build
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:5173
- To use a real local Gemma model instead of mock mode:
  ```bash
  docker exec -it ai-gateway-ollama-1 ollama pull gemma3:4b
  ```

## Quickstart (local dev, no Docker)

```bash
# backend
cd backend
pip install -r requirements.txt --break-system-packages
uvicorn app.main:app --reload

# frontend (separate terminal)
cd frontend
npm install
npm run dev
```
SQLite is used automatically when `DATABASE_URL` isn't set to Postgres, and Redis falls back to an in-memory shim if unreachable — so `uvicorn app.main:app --reload` alone is enough to try the backend.

---

## Verifying it works

```bash
# create an org + API key
curl -X POST localhost:8000/v1/admin/organizations -d '{"name":"Acme"}' -H 'Content-Type: application/json'
# -> use the returned admin_token to create an API key at POST /v1/admin/api-keys

# send a request
curl -X POST localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <api_key>" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Write a function that reverses a string"}]}'
```

## Running tests

```bash
cd backend && pytest tests/ -v   # 39 tests: unit (agents/policy) + integration (full API)
```

---

## Project structure

See [`docs/phase8-project-structure.md`](./docs/phase8-project-structure.md) for the full annotated layout. Top level:

```
backend/    FastAPI app: routing engine, providers, cache, DB, API routes, tests
frontend/   React + TS + Vite + Tailwind console (Playground + Dashboard)
docs/       All 13 phase deliverables (product discovery through deployment)
docker-compose.yml
```

## Design documents

| Phase | Document |
|---|---|
| 1. Product Discovery | [docs/phase1-product-discovery.md](./docs/phase1-product-discovery.md) |
| 2. SRS | [docs/phase2-srs.md](./docs/phase2-srs.md) |
| 3. AI System Design | [docs/phase3-ai-system-design.md](./docs/phase3-ai-system-design.md) |
| 4. System Architecture | [docs/phase4-system-architecture.md](./docs/phase4-system-architecture.md) |
| 5. Database Design | [docs/phase5-database-design.md](./docs/phase5-database-design.md) |
| 6. API Design | [docs/phase6-api-design.md](./docs/phase6-api-design.md) |
| 7. Frontend Design | [docs/phase7-frontend-design.md](./docs/phase7-frontend-design.md) |
| 8. Project Structure | [docs/phase8-project-structure.md](./docs/phase8-project-structure.md) |
| 9. Development Roadmap | [docs/phase9-development-roadmap.md](./docs/phase9-development-roadmap.md) |

## Honest scope notes (what's real vs. what's simplified for hackathon time)

- **Real and tested**: the full routing pipeline (intent/complexity/risk/token/cost/latency/confidence agents), LangGraph orchestration with retry/fallback, exact + semantic caching, budget-pressure-aware routing, explainability traces, auth, rate limiting, analytics — all covered by 39 passing unit + integration tests.
- **Mocked by design, not by omission**: cloud provider responses run in a clearly-labeled mock mode when no API key is set, so the system is demoable without burning quota; swap in real keys and it calls the real APIs via LiteLLM.
- **Simplified vs. the original design docs**: intent/complexity/risk agents use fast heuristics rather than trained classifiers (documented as the swap-in point in `docs/phase3-ai-system-design.md`); Alembic migrations are stubbed with `create_all` for one-command startup; the frontend ships the two screens that matter for the demo (Playground, Dashboard) rather than all nine designed in Phase 7 — Admin/Auth/Policy screens are fully served by the backend API and documented, just not built as UI yet.
