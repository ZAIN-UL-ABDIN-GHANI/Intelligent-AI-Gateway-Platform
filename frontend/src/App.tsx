import { useState } from "react";
import { api, ChatResponse } from "./lib/apiClient";
import RoutingManifest, { ManifestEntry } from "./components/RoutingManifest";
import Playground from "./components/Playground";
import Dashboard from "./components/Dashboard";

type Tab = "playground" | "dashboard";

export default function App() {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [orgName, setOrgName] = useState("");
  const [busy, setBusy] = useState(false);
  const [setupError, setSetupError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("playground");
  const [manifest, setManifest] = useState<ManifestEntry[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);

  async function handleBootstrap() {
    if (!orgName.trim()) return;
    setBusy(true);
    setSetupError(null);
    try {
      const org = await api.bootstrapOrg(orgName.trim());
      const key = await api.createApiKey(org.admin_token, "console");
      setApiKey(key.key);
    } catch {
      setSetupError("Could not reach the gateway. Is the backend running?");
    } finally {
      setBusy(false);
    }
  }

  function handleNewTrace(r: ChatResponse) {
    setManifest((prev) =>
      [
        { trace_id: r.trace_id, backend: r.routed_model, intent: "request", cost: r.usage.cost, cache_hit: r.cache_hit },
        ...prev,
      ].slice(0, 12)
    );
    setRefreshKey((k) => k + 1);
  }

  if (!apiKey) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="max-w-sm w-full space-y-4">
          <div>
            <p className="font-mono text-xs uppercase tracking-widest text-gemma mb-2">AI Gateway</p>
            <h1 className="text-2xl font-semibold">Routing console</h1>
            <p className="text-sm text-muted mt-1">Name your organization to spin up a demo API key.</p>
          </div>
          <input
            className="w-full bg-surface border border-border rounded-md p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gemma"
            placeholder="Organization name (e.g. Acme Inc)"
            value={orgName}
            onChange={(e) => setOrgName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleBootstrap()}
            aria-label="Organization name"
          />
          {setupError && <p className="text-sm text-red-400">{setupError}</p>}
          <button
            onClick={handleBootstrap}
            disabled={busy}
            className="w-full bg-gemma text-base font-semibold rounded-md py-2.5 text-sm hover:opacity-90 disabled:opacity-50 transition"
          >
            {busy ? "Setting up…" : "Enter console"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-border px-6 py-4 flex items-center justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-gemma">AI Gateway</p>
          <h1 className="text-lg font-semibold">Routing console</h1>
        </div>
        <nav className="flex gap-1 bg-surface border border-border rounded-md p-1">
          {(["playground", "dashboard"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-1.5 rounded text-sm capitalize transition ${
                tab === t ? "bg-gemma text-base font-semibold" : "text-muted hover:text-ink"
              }`}
            >
              {t}
            </button>
          ))}
        </nav>
      </header>

      <RoutingManifest entries={manifest} />

      <main className="flex-1 px-6 py-8 max-w-6xl mx-auto w-full">
        {tab === "playground" ? (
          <Playground apiKey={apiKey} onNewTrace={handleNewTrace} />
        ) : (
          <Dashboard apiKey={apiKey} refreshKey={refreshKey} />
        )}
      </main>
    </div>
  );
}
