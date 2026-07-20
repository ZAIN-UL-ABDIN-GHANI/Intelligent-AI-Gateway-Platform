# Phase 11 — Testing
## Enterprise AI Gateway: Hybrid Token-Efficient Routing Agent

This phase is implemented, not just planned — 39 tests exist in `backend/tests/` and pass (`pytest tests/ -v`).

---

## 1. Unit Tests (`tests/unit/`)
Cover each routing agent in isolation, independent of the API or database:
- `test_intent.py` — 7 tests verifying intent classification (code/summarization/extraction/creative/reasoning/qa/chat).
- `test_complexity.py` — 4 tests verifying complexity scoring responds correctly to length, multi-step language, and code blocks, and stays bounded [0,1].
- `test_risk.py` — 5 tests verifying PII/risk detection (none/low/high) across email, SSN, credit card, and secret-key patterns.
- `test_token_predictor.py` — 4 tests on input/output token estimation behavior.
- `test_cost_predictor.py` — 3 tests on cost calculation, including the local-model-is-free invariant.
- `test_policy.py` — 6 tests on eligibility filtering (privacy policy, health, context window) and score ordering.

## 2. Integration Tests (`tests/integration/test_chat_api.py`)
Exercise the full FastAPI app via `TestClient`, including DB and cache layers:
- Auth required / rejected without a valid key.
- Full chat completion end-to-end (routing → mock provider call → trace persisted → response returned).
- Exact-cache hit on an identical second request.
- Validation rejects empty/whitespace-only prompts.
- High-risk (PII) prompts are force-routed to the local backend.
- Trace retrieval returns the full explainability payload.
- Feedback submission updates the confidence table.
- Cost analytics reflect actual recorded trace costs.
- Cross-org trace access is forbidden (403).

## 3. API Tests
The integration suite above doubles as API contract testing since it exercises the real HTTP routes through FastAPI's TestClient rather than calling internal functions directly.

## 4. Load Tests (planned, not yet automated)
Recommended tool: `locust` or `k6` against `/v1/chat/completions` with `force_backend=gemma-local` to isolate gateway overhead from provider latency. Target: NFR-1 (routing overhead < 100ms p95) and the ≥50 concurrent request goal from Phase 2 §9. Not included in this build to stay within hackathon time; the seam is clean (stateless FastAPI + Redis/Postgres) so it's a config-only addition.

## 5. Performance Tests
Manual verification during development: chat completion round-trip in mock mode consistently returns in well under 100ms of gateway-added overhead (mock provider calls are near-instant; real provider calls will dominate total latency, which is expected and by design — the router adds negligible overhead).

## 6. Security Tests
Covered by integration tests: unauthorized requests rejected (401), cross-org data access rejected (403). Not yet automated: rate-limit-exceeded (429) test and injected-header/malformed-JWT fuzz tests — straightforward additions using the existing `check_rate_limit`/`decode_access_token` seams.

## 7. AI Evaluation Tests
`test_policy.py::test_high_risk_strict_policy_restricts_to_local` and the integration test `test_high_risk_prompt_routes_locally` together constitute the core "AI evaluation" test for this system: they assert the routing decision itself is correct for a safety-critical case, not just that the HTTP layer works. Additional recommended (not yet built) AI-eval tests: a labeled set of ~50 prompts with expected intent/backend to track routing-accuracy regression over time as agents evolve.

---

**Next:** Phase 12 — Deployment.
