# Phase 9 — Development Roadmap
## Enterprise AI Gateway: Hybrid Token-Efficient Routing Agent

Milestones sized for a hackathon build (roughly a 2-day / 20-hour core build + polish).

---

### Milestone 1 — Foundation & Data Layer (3h)
- **Objective**: DB schema live, FastAPI skeleton running, Docker Compose up.
- **Files**: `db/models.py`, `migrations/`, `main.py`, `config.py`, `docker-compose.yml`.
- **Dependencies**: none.
- **APIs**: `/v1/health`.
- **Testing**: DB connects, migration applies cleanly, health check returns 200.
- **Est. hours**: 3

### Milestone 2 — Provider Integration (3h)
- **Objective**: LiteLLM wrappers for Gemma (local via Ollama), Claude, GPT, Gemini all callable with a uniform interface.
- **Files**: `providers/*.py`.
- **Dependencies**: M1, provider API keys, Ollama running Gemma.
- **APIs**: internal only.
- **Testing**: unit tests mocking each provider call; one live smoke test per provider.
- **Est. hours**: 3

### Milestone 3 — Routing Engine Core (5h)
- **Objective**: LangGraph flow with all scoring agents (Phase 3) and decision logic wired end-to-end.
- **Files**: `routing/graph.py`, `routing/agents/*.py`, `routing/policy.py`.
- **Dependencies**: M2.
- **APIs**: none yet (internal function callable from tests).
- **Testing**: unit tests per agent + integration test of full graph on sample prompts (verify code prompt → claude/gpt, simple chat → gemma, PII prompt → local-only).
- **Est. hours**: 5

### Milestone 4 — Chat Completions API + Caching (3h)
- **Objective**: `/v1/chat/completions` live end-to-end with exact + semantic caching.
- **Files**: `api/chat.py`, `cache/exact_cache.py`, `cache/semantic_cache.py`.
- **Dependencies**: M1–M3.
- **APIs**: `POST /v1/chat/completions`.
- **Testing**: integration tests incl. cache hit/miss, fallback on simulated provider failure.
- **Est. hours**: 3

### Milestone 5 — Traces, Feedback, Analytics APIs (2h)
- **Objective**: explainability + analytics endpoints backed by real trace data.
- **Files**: `api/traces.py`, `api/feedback.py`, `api/analytics.py`.
- **Dependencies**: M4.
- **APIs**: `/v1/traces/{id}`, `/v1/feedback`, `/v1/analytics/*`.
- **Testing**: API tests asserting cost sums match trace records.
- **Est. hours**: 2

### Milestone 6 — Auth, Admin, Rate Limiting (2h)
- **Objective**: API key auth, org/key management, Redis rate limiting.
- **Files**: `core/security.py`, `core/rate_limit.py`, `api/admin.py`.
- **Dependencies**: M1.
- **APIs**: `/v1/admin/*`.
- **Testing**: unauthorized/rate-limited request tests.
- **Est. hours**: 2

### Milestone 7 — Frontend Dashboard (4h)
- **Objective**: Dashboard, Trace Detail, Analytics, Playground screens functional against real API.
- **Files**: `frontend/src/**`.
- **Dependencies**: M4–M6 deployed locally.
- **APIs**: consumes all above.
- **Testing**: manual QA pass + a handful of component tests on chart rendering.
- **Est. hours**: 4

### Milestone 8 — Deployment & Docs Polish (2h)
- **Objective**: full docker-compose demo runs one command, README/quickstart works for a fresh judge machine.
- **Files**: `docker-compose.yml`, `README.md`, `.env.example`, CI workflow.
- **Dependencies**: all above.
- **Testing**: clean-machine run-through.
- **Est. hours**: 2

**Total estimate: ~24 hours core build**, leaving buffer for bonus features (streaming, multi-org, RAG) if time remains — explicitly time-boxed as stretch, not committed.

---

**Next:** Phase 10 — Implementation (code, module by module, starting with Milestone 1).
