# Phase 8 — Project Structure
## Enterprise AI Gateway: Hybrid Token-Efficient Routing Agent

```
ai-gateway/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entrypoint, router registration
│   │   ├── config.py                # env-based settings (pydantic-settings)
│   │   ├── deps.py                  # shared FastAPI dependencies (auth, db session)
│   │   ├── api/
│   │   │   ├── chat.py              # POST /v1/chat/completions
│   │   │   ├── traces.py            # GET /v1/traces/{id}
│   │   │   ├── feedback.py          # POST /v1/feedback
│   │   │   ├── analytics.py         # /v1/analytics/*
│   │   │   ├── admin.py             # /v1/admin/*
│   │   │   └── health.py            # /v1/health, /v1/metrics
│   │   ├── routing/
│   │   │   ├── graph.py             # LangGraph state machine wiring
│   │   │   ├── agents/
│   │   │   │   ├── intent.py
│   │   │   │   ├── complexity.py
│   │   │   │   ├── risk.py
│   │   │   │   ├── token_predictor.py
│   │   │   │   ├── cost_predictor.py
│   │   │   │   ├── latency_predictor.py
│   │   │   │   ├── confidence.py
│   │   │   │   └── decision.py
│   │   │   └── policy.py            # scoring weights, eligibility filters
│   │   ├── providers/
│   │   │   ├── litellm_client.py    # unified call wrapper
│   │   │   ├── gemma_local.py
│   │   │   ├── claude_provider.py
│   │   │   ├── gpt_provider.py
│   │   │   └── gemini_provider.py
│   │   ├── cache/
│   │   │   ├── exact_cache.py       # Redis exact-match
│   │   │   └── semantic_cache.py    # FAISS similarity
│   │   ├── db/
│   │   │   ├── models.py            # SQLAlchemy models
│   │   │   ├── session.py
│   │   │   └── crud.py
│   │   ├── schemas/
│   │   │   ├── chat.py              # Pydantic request/response models
│   │   │   ├── trace.py
│   │   │   └── admin.py
│   │   └── core/
│   │       ├── security.py          # API key hashing, JWT
│   │       ├── logging.py
│   │       └── rate_limit.py
│   ├── migrations/                  # Alembic migrations
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── pages/
│   │   ├── components/
│   │   ├── lib/apiClient.ts
│   │   └── styles/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── phase1-product-discovery.md ... phase13-documentation.md
│   ├── ARCHITECTURE.md
│   └── API.md
├── .github/workflows/ci.yml
└── README.md
```

### Folder rationale
- `app/api/` — thin HTTP layer only; no business logic, delegates to `routing/`, `providers/`, `db/`.
- `app/routing/agents/` — one file per agent from Phase 3, independently unit-testable.
- `app/providers/` — isolates provider SDK quirks behind one interface so adding a 5th model later touches only this folder.
- `app/cache/` — two cache tiers kept separate since they have different correctness/risk trade-offs (semantic cache must respect risk level).
- `migrations/` — Alembic, never hand-edit the DB schema directly.
- `frontend/src/pages` vs `components` — pages are route-level containers; components are reusable/presentational, matching the component tree in Phase 7.
- `docs/` — all phase deliverables kept in the repo as living documentation, not just hackathon submission artifacts.

---

**Next:** Phase 9 — Development Roadmap.
