const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export interface ChatResponse {
  id: string;
  trace_id: string;
  routed_model: string;
  content: string;
  usage: { input_tokens: number; output_tokens: number; cost: number };
  cache_hit: boolean;
}

export interface TraceDetail {
  trace_id: string;
  intent: string;
  complexity_score: number;
  risk_level: string;
  candidate_scores: Record<string, number>;
  chosen_backend: string;
  reason: string;
  cost: number;
  latency_ms: number;
  cache_hit: boolean;
}

export interface CostBreakdown {
  total_cost: number;
  breakdown: { backend: string; cost: number }[];
}

export interface RoutingDistribution {
  distribution: { backend: string; count: number; share: number }[];
}

async function request<T>(path: string, apiKey: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.error?.message || body?.detail?.message || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  bootstrapOrg: async (name: string) => {
    const res = await fetch(`${API_BASE}/v1/admin/organizations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, privacy_policy: "strict" }),
    });
    return res.json() as Promise<{ org_id: string; name: string; admin_token: string }>;
  },
  createApiKey: async (adminToken: string, label: string) => {
    const res = await fetch(`${API_BASE}/v1/admin/api-keys`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${adminToken}` },
      body: JSON.stringify({ label }),
    });
    return res.json() as Promise<{ key: string; key_id: string }>;
  },
  chatCompletion: (apiKey: string, prompt: string, forceBackend?: string) =>
    request<ChatResponse>("/v1/chat/completions", apiKey, {
      method: "POST",
      body: JSON.stringify({
        messages: [{ role: "user", content: prompt }],
        model: forceBackend ? forceBackend : "auto",
        force_backend: forceBackend,
      }),
    }),
  getTrace: (apiKey: string, traceId: string) => request<TraceDetail>(`/v1/traces/${traceId}`, apiKey),
  costAnalytics: (apiKey: string) => request<CostBreakdown>("/v1/analytics/cost", apiKey),
  routingDistribution: (apiKey: string) =>
    request<RoutingDistribution>("/v1/analytics/routing-distribution", apiKey),
  sendFeedback: (apiKey: string, traceId: string, rating: "up" | "down") =>
    request("/v1/feedback", apiKey, {
      method: "POST",
      body: JSON.stringify({ trace_id: traceId, rating }),
    }),
};
