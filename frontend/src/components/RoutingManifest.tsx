import { backendMeta } from "../lib/backends";

export interface ManifestEntry {
  trace_id: string;
  backend: string;
  intent: string;
  cost: number;
  cache_hit: boolean;
}

export default function RoutingManifest({ entries }: { entries: ManifestEntry[] }) {
  if (entries.length === 0) {
    return (
      <div className="border-y border-border bg-surface py-2.5 px-4 font-mono text-xs text-muted">
        NO TRAFFIC YET — send a request in the Playground to populate the manifest
      </div>
    );
  }

  const doubled = [...entries, ...entries];

  return (
    <div className="border-y border-border bg-surface overflow-hidden whitespace-nowrap py-2.5">
      <div className="inline-flex animate-ticker">
        {doubled.map((e, i) => {
          const meta = backendMeta(e.backend);
          return (
            <span key={`${e.trace_id}-${i}`} className="inline-flex items-center gap-2 px-6 font-mono text-xs">
              <span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />
              <span className={`font-semibold ${meta.color}`}>{meta.label}</span>
              <span className="text-muted">→</span>
              <span className="text-ink/80 uppercase">{e.intent}</span>
              <span className="text-muted">·</span>
              <span className="text-ink/60">${e.cost.toFixed(5)}</span>
              {e.cache_hit && <span className="text-good">· CACHED</span>}
            </span>
          );
        })}
      </div>
    </div>
  );
}
