import { useState } from "react";
import { api, ChatResponse, TraceDetail } from "../lib/apiClient";
import { backendMeta } from "../lib/backends";

const FORCE_OPTIONS = [
  { value: "", label: "Auto (let the router decide)" },
  { value: "gemma-local", label: "Force: Gemma (local)" },
  { value: "claude", label: "Force: Claude" },
  { value: "gpt", label: "Force: GPT" },
  { value: "gemini", label: "Force: Gemini" },
];

export default function Playground({
  apiKey,
  onNewTrace,
}: {
  apiKey: string;
  onNewTrace: (r: ChatResponse) => void;
}) {
  const [prompt, setPrompt] = useState("Write a Python function that reverses a string, step by step.");
  const [forceBackend, setForceBackend] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [trace, setTrace] = useState<TraceDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSend() {
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);
    setResponse(null);
    setTrace(null);
    try {
      const res = await api.chatCompletion(apiKey, prompt, forceBackend || undefined);
      setResponse(res);
      onNewTrace(res);
      const t = await api.getTrace(apiKey, res.trace_id);
      setTrace(t);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function sendFeedback(rating: "up" | "down") {
    if (!response) return;
    try {
      await api.sendFeedback(apiKey, response.trace_id, rating);
    } catch {
      setError("Failed to submit feedback");
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
      <div className="lg:col-span-2 space-y-3">
        <label className="text-xs font-mono uppercase tracking-wide text-muted">Prompt</label>
        <textarea
          className="w-full h-40 bg-surface border border-border rounded-md p-3 font-mono text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gemma resize-none"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          aria-label="Prompt input"
        />
        <select
          className="w-full bg-surface border border-border rounded-md p-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-gemma"
          value={forceBackend}
          onChange={(e) => setForceBackend(e.target.value)}
          aria-label="Backend selection"
        >
          {FORCE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <button
          onClick={handleSend}
          disabled={loading}
          className="w-full bg-gemma text-base font-semibold rounded-md py-2.5 text-sm hover:opacity-90 disabled:opacity-50 transition"
        >
          {loading ? "Routing…" : "Send request"}
        </button>
        {error && <p className="text-bad text-sm font-mono">{error}</p>}
      </div>

      <div className="lg:col-span-3 space-y-4">
        <div className="border border-border rounded-md bg-surface p-4 min-h-[8rem]">
          <p className="text-xs font-mono uppercase tracking-wide text-muted mb-2">Response</p>
          {response ? (
            <>
              <p className="text-sm whitespace-pre-wrap">{response.content}</p>
              <div className="flex items-center gap-3 mt-4">
                <button onClick={() => sendFeedback("up")} className="text-xs font-mono text-good hover:underline">
                  👍 good routing
                </button>
                <button onClick={() => sendFeedback("down")} className="text-xs font-mono text-bad hover:underline">
                  👎 bad routing
                </button>
              </div>
            </>
          ) : (
            <p className="text-sm text-muted">Send a prompt to see the routed response here.</p>
          )}
        </div>

        {trace && (
          <div className="border border-border rounded-md bg-surface p-4">
            <p className="text-xs font-mono uppercase tracking-wide text-muted mb-3">Routing explanation</p>
            <div className="grid grid-cols-2 gap-3 text-xs font-mono mb-3">
              <div><span className="text-muted">intent</span> <span className="text-ink">{trace.intent}</span></div>
              <div><span className="text-muted">complexity</span> <span className="text-ink">{trace.complexity_score.toFixed(2)}</span></div>
              <div><span className="text-muted">risk</span> <span className="text-ink">{trace.risk_level}</span></div>
              <div><span className="text-muted">latency</span> <span className="text-ink">{trace.latency_ms}ms</span></div>
            </div>
            <p className="text-xs font-mono text-muted mb-3">{trace.reason}</p>
            <div className="space-y-1.5">
              {Object.entries(trace.candidate_scores)
                .sort((a, b) => b[1] - a[1])
                .map(([backend, score]) => {
                  const meta = backendMeta(backend);
                  const isWinner = backend === trace.chosen_backend;
                  return (
                    <div key={backend} className="flex items-center gap-2">
                      <span className={`w-24 text-xs font-mono ${meta.color}`}>{meta.label}</span>
                      <div className="flex-1 h-2 bg-surface2 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${meta.dot} ${isWinner ? "" : "opacity-40"}`}
                          style={{ width: `${Math.max(score, 0) * 100}%` }}
                        />
                      </div>
                      <span className="w-12 text-right text-xs font-mono text-ink/70">{score.toFixed(2)}</span>
                      {isWinner && <span className="text-xs text-good">✓</span>}
                    </div>
                  );
                })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
