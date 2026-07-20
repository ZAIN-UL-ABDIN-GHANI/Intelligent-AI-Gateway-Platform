# Phase 2 — System Requirements Specification (SRS)
## Enterprise AI Gateway: Hybrid Token-Efficient Routing Agent
IEEE 830-style specification

---

## 1. Introduction

### 1.1 Purpose
Specifies functional and non-functional requirements for the AI Gateway, a service that receives chat/completion requests and intelligently routes them across local (Gemma) and cloud (Claude, GPT, Gemini) models.

### 1.2 Scope
Covers the gateway API, routing engine, caching, storage, dashboard, and admin/auth surfaces defined in Phase 1 scope. Excludes fine-tuned learned routing models and enterprise SSO (post-MVP).

### 1.3 Definitions
- **Router**: component deciding which backend model handles a request.
- **Backend**: a concrete model endpoint (local Gemma, Claude API, GPT API, Gemini API).
- **Routing trace**: structured record of why a decision was made.
- **Org**: a tenant/customer using the gateway.

### 1.4 References
OpenAI Chat Completions API spec, Anthropic Messages API spec, Google Gemini API spec (used for compatibility shaping of the gateway's public API).

---

## 2. Overall Description

### 2.1 Product Perspective
Sits as a reverse-proxy/middleware between client applications and model providers. Stateless compute layer + Postgres for persistence + Redis for cache/session/rate-limit state + FAISS for semantic cache similarity search.

### 2.2 Product Functions
Request ingestion → feature extraction (complexity, intent, PII/risk, token estimate) → routing decision → backend call with retry/fallback → response + trace logging → analytics aggregation.

### 2.3 User Classes
- **Developer/Integrator** (API consumer, uses API keys)
- **Org Admin** (configures policy, budgets, views dashboards)
- **Platform Admin** (manages orgs, global settings)

### 2.4 Operating Environment
Docker Compose (dev/demo) or Kubernetes (production stretch). Linux containers. Local model served via Ollama-compatible OpenAI-shaped endpoint.

### 2.5 Design/Implementation Constraints
FastAPI/Python backend, React/TS frontend, PostgreSQL, Redis, FAISS, LangGraph/LangChain for agent orchestration, LiteLLM for unified provider calls.

### 2.6 Assumptions & Dependencies
As per Phase 1 §17–18. Availability of provider API keys; local model reachable via HTTP.

---

## 3. Functional Requirements

| ID | Requirement |
|---|---|
| FR-1 | System shall expose an OpenAI-compatible `POST /v1/chat/completions` endpoint. |
| FR-2 | System shall compute a complexity score (0–1) for each incoming prompt. |
| FR-3 | System shall estimate input+output token counts before routing. |
| FR-4 | System shall classify PII/sensitivity risk (none/low/high) per prompt. |
| FR-5 | System shall detect intent category (e.g., code, summarization, creative, QA, extraction). |
| FR-6 | System shall select a backend model using a documented routing policy combining FR-2–FR-5, org config, and live provider health. |
| FR-7 | System shall force-route high-risk/PII-flagged prompts to local-only backends unless org explicitly opts out. |
| FR-8 | System shall retry on a different backend if the selected backend errors or times out. |
| FR-9 | System shall cache semantically similar prompts (via FAISS) and return cached responses when similarity exceeds a configurable threshold. |
| FR-10 | System shall log a routing trace (inputs, scores, chosen model, reason, cost, latency) per request. |
| FR-11 | System shall expose analytics endpoints for cost, token usage, and routing distribution, filterable by org/date/model. |
| FR-12 | System shall support per-org budget thresholds that bias routing toward cheaper backends as budget is consumed. |
| FR-13 | System shall support API key-based authentication per org. |
| FR-14 | System shall support streaming responses (SSE) from backends that support it. |
| FR-15 | System shall support optional conversation memory (multi-turn context) scoped per session. |
| FR-16 | System shall accept explicit user feedback (thumbs up/down) tied to a routing trace for future learning. |

---

## 4. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | Routing decision overhead shall be < 100ms at p95, excluding backend model latency. |
| NFR-2 | Gateway shall be horizontally scalable; no in-memory session state outside Redis. |
| NFR-3 | Gateway uptime target 99.9% excluding upstream provider outages. |
| NFR-4 | All routing traces shall be persisted for at least the org's configured retention period. |
| NFR-5 | PII-flagged content shall never be transmitted to a non-approved external backend. |
| NFR-6 | API keys and provider secrets shall be stored encrypted at rest. |
| NFR-7 | System shall degrade gracefully (mocked/deterministic responses) when provider quota is exhausted, for demo resilience. |
| NFR-8 | Dashboard queries shall return in < 2s for 30-day windows on demo-scale data. |

---

## 5. Interfaces

- **REST API** (FastAPI, OpenAPI 3 spec auto-generated) — primary integration surface.
- **Web Dashboard** (React) — human interface for admins.
- **Provider interfaces** — LiteLLM-mediated calls to Anthropic, OpenAI, Google, and local Gemma (Ollama OpenAI-compatible endpoint).

---

## 6. User Stories & Acceptance Criteria

**US-1**: As a developer, I want to call one endpoint and have it pick the best model, so I don't hardcode routing logic.
- AC: `POST /v1/chat/completions` with no `model` override returns a response and an `X-Routed-Model` header, in under [latency budget] + model latency.

**US-2**: As a compliance engineer, I want PII-containing prompts to never reach external APIs.
- AC: Given a prompt flagged high-risk by the PII classifier, the routing trace shows only local backends were eligible, and the response header confirms local execution.

**US-3**: As an org admin, I want to see this month's spend by model.
- AC: `GET /v1/analytics/cost?org_id=...&range=30d` returns per-model totals matching the sum of routing trace costs.

**US-4**: As a developer, I want automatic failover if my usual model is down.
- AC: Simulated 500/timeout from primary backend results in a retry on a fallback backend within one request cycle, transparent to the caller.

---

## 7. Use Cases

**UC-1: Route a standard chat request**
Actor: Client app. Flow: request → feature extraction → policy evaluation → backend call → response + trace log. Alternate: backend failure → fallback backend → response.

**UC-2: Force-local routing for sensitive data**
Actor: Client app submitting a prompt containing PII. Flow: PII classifier flags high risk → router restricts candidate set to local backends → local Gemma handles request.

**UC-3: Admin reviews cost dashboard**
Actor: Org admin. Flow: login → dashboard queries analytics API → charts render cost/token/model-share.

**UC-4: Budget-aware routing**
Actor: System (background). Flow: org nears monthly budget threshold → router weighting shifts toward cheaper/local backends automatically until reset.

---

## 8. Edge Cases & Error Conditions

- Empty/whitespace-only prompt → 400 validation error.
- All backends unavailable → 503 with retry-after header, trace logged as `all_backends_failed`.
- Token estimate exceeds model context window → reject or auto-route to a large-context backend.
- Conflicting org policy (e.g., budget forces local, but content requires capability only cloud has) → policy priority order documented and applied (privacy > budget > quality, configurable).
- Cache hit on stale/changed knowledge-sensitive query → similarity threshold tuned conservatively; cache bypass flag supported per request.
- Streaming request to a backend without streaming support → gateway buffers and simulates chunked delivery.

---

## 9. Performance Goals
See NFR-1, NFR-3, NFR-8. Additional: system shall sustain ≥ 50 concurrent requests in demo load test without routing-layer errors.

## 10. Security Requirements
API-key auth per org; secrets encrypted at rest (e.g., via environment-injected KMS or Docker secrets in dev); rate limiting per API key (Redis token bucket); audit log immutability (append-only trace table); input sanitization against prompt-injection targeting the router's own classifier prompts.

## 11. Privacy Requirements
PII classifier runs pre-routing on every request; high-risk prompts restricted to local backend(s) by default; org-level data residency flag; configurable trace retention with redaction option for stored prompt text.

---

**Next:** Phase 3 — AI System Design (routing logic, LangGraph flow, scoring agents).
