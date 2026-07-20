# Phase 6 — API Design
## Enterprise AI Gateway: Hybrid Token-Efficient Routing Agent

All endpoints prefixed `/v1`. Auth via `Authorization: Bearer <api_key>` unless noted. All responses JSON. Standard error envelope:

```json
{ "error": { "code": "string", "message": "string", "trace_id": "uuid|null" } }
```

---

## 1. `POST /v1/chat/completions`
OpenAI-compatible chat completion, transparently routed.

**Request**
```json
{
  "messages": [{"role": "user", "content": "string"}],
  "model": "auto | gemma-local | claude | gpt | gemini",
  "stream": false,
  "session_id": "string (optional)",
  "force_backend": "string (optional, overrides routing)"
}
```
**Response 200**
```json
{
  "id": "trace_uuid",
  "choices": [{"message": {"role": "assistant", "content": "string"}}],
  "routed_model": "gemma-local",
  "usage": {"input_tokens": 120, "output_tokens": 45, "cost": 0.0003},
  "cache_hit": false,
  "trace_id": "uuid"
}
```
**Validation**: `messages` non-empty; total estimated tokens ≤ max context of any eligible backend, else `400 context_window_exceeded`.
**Errors**: `400 invalid_request`, `401 unauthorized`, `429 rate_limited`, `503 all_backends_unavailable`.
**Auth**: required. **Rate limit**: per-org token bucket (default 60 req/min, configurable).

---

## 2. `GET /v1/traces/{trace_id}`
Full explainability record for a routing decision.

**Response 200**
```json
{
  "trace_id": "uuid",
  "intent": "code",
  "complexity_score": 0.72,
  "risk_level": "none",
  "candidate_scores": {"gemma-local": 0.51, "claude": 0.88, "gpt": 0.83, "gemini": 0.79},
  "chosen_backend": "claude",
  "reason": "highest quality-confidence for intent=code, within budget",
  "cost": 0.004,
  "latency_ms": 812
}
```
**Errors**: `404 trace_not_found`, `403 forbidden` (trace belongs to another org). **Auth**: required.

---

## 3. `POST /v1/feedback`
Submit feedback on a prior response.

**Request**: `{"trace_id": "uuid", "rating": "up|down", "comment": "string (optional)"}`
**Response 201**: `{"id": "uuid", "status": "recorded"}`
**Errors**: `400 invalid_rating`, `404 trace_not_found`. **Auth**: required.

---

## 4. `GET /v1/analytics/cost`
**Query params**: `org_id` (implicit from key), `range` (`7d|30d|90d`), `group_by` (`backend|day`)
**Response 200**: `{"range": "30d", "total_cost": 42.17, "breakdown": [{"backend": "gemma-local", "cost": 0.0}, {"backend": "claude", "cost": 31.40}]}`
**Auth**: required (org admin role for cross-user visibility).

## 5. `GET /v1/analytics/tokens`
Same shape as cost, token counts instead. **Auth**: required.

## 6. `GET /v1/analytics/routing-distribution`
Returns share of traffic per backend/intent, for the dashboard's routing pie/bar charts. **Auth**: required.

---

## 7. `POST /v1/admin/api-keys`
Create an API key for an org. **Auth**: admin session (not API key) — user JWT from dashboard login.
**Request**: `{"org_id": "uuid", "label": "string"}`
**Response 201**: `{"key": "plaintext-shown-once", "key_id": "uuid"}`

## 8. `DELETE /v1/admin/api-keys/{key_id}`
Revoke a key. **Response 204**.

## 9. `PUT /v1/admin/budget`
Set/update org monthly budget. **Request**: `{"org_id": "uuid", "monthly_limit": 500.00}`. **Response 200**.

## 10. `PUT /v1/admin/policy`
Set org routing policy (weights, privacy strictness). **Request**: `{"org_id": "uuid", "privacy_policy": "strict|balanced|open", "weights": {"quality":0.4,"cost":0.3,"latency":0.2,"budget":0.1}}`. **Response 200**.

## 11. `GET /v1/health`
Liveness/readiness probe, no auth. Returns per-backend health status (used by router eligibility filter).

```json
{"status": "ok", "backends": {"gemma-local": "healthy", "claude": "healthy", "gpt": "degraded", "gemini": "healthy"}}
```

## 12. `GET /v1/metrics`
Prometheus-format metrics, no auth (typically network-restricted).

---

## 13. Authentication & Authorization
Two tiers: **API keys** (service-to-service, `chat/completions`, `traces`, `feedback`, `analytics` read) and **User JWT sessions** (dashboard login, needed for `/admin/*` and cross-user analytics). Roles: `member` (own usage only), `org_admin` (org-wide), `platform_admin` (all orgs).

## 14. Rate Limiting
Redis token-bucket per API key: default 60 req/min burst 20, configurable per org tier; `429` responses include `Retry-After` header.

---

**Next:** Phase 7 — Frontend Design (dashboard, screens, component tree).
