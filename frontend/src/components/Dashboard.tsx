import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from "recharts";
import { api, CostBreakdown, RoutingDistribution } from "../lib/apiClient";
import { backendMeta } from "../lib/backends";

const COLOR_HEX: Record<string, string> = {
  "gemma-local": "#2DD4BF",
  claude: "#FB7A5D",
  gpt: "#6366F1",
  gemini: "#F5A623",
};

export default function Dashboard({ apiKey, refreshKey }: { apiKey: string; refreshKey: number }) {
  const [cost, setCost] = useState<CostBreakdown | null>(null);
  const [dist, setDist] = useState<RoutingDistribution | null>(null);

  useEffect(() => {
    api.costAnalytics(apiKey).then(setCost).catch(() => {});
    api.routingDistribution(apiKey).then(setDist).catch(() => {});
  }, [apiKey, refreshKey]);

  const totalRequests = dist?.distribution.reduce((sum, d) => sum + d.count, 0) || 0;
  const localShare = dist?.distribution.find((d) => d.backend === "gemma-local")?.share || 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Total cost" value={`$${(cost?.total_cost || 0).toFixed(4)}`} />
        <KpiCard label="Total requests" value={String(totalRequests)} />
        <KpiCard label="Local model share" value={`${(localShare * 100).toFixed(0)}%`} accent="text-gemma" />
        <KpiCard label="Backends active" value={String(dist?.distribution.length || 0)} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="border border-border rounded-md bg-surface p-4">
          <p className="text-xs font-mono uppercase tracking-wide text-muted mb-4">Routing distribution</p>
          {dist && dist.distribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={dist.distribution}
                  dataKey="count"
                  nameKey="backend"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                >
                  {dist.distribution.map((d) => (
                    <Cell key={d.backend} fill={COLOR_HEX[d.backend] || "#7C8699"} stroke="none" />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "#131720", border: "1px solid #232938", fontSize: 12 }}
                  labelStyle={{ color: "#E4E7EB" }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-muted py-16 text-center">No routing data yet</p>
          )}
          <div className="flex flex-wrap gap-3 mt-2">
            {dist?.distribution.map((d) => {
              const meta = backendMeta(d.backend);
              return (
                <span key={d.backend} className="flex items-center gap-1.5 text-xs font-mono">
                  <span className={`h-2 w-2 rounded-full ${meta.dot}`} />
                  <span className={meta.color}>{meta.label}</span>
                  <span className="text-muted">{(d.share * 100).toFixed(0)}%</span>
                </span>
              );
            })}
          </div>
        </div>

        <div className="border border-border rounded-md bg-surface p-4">
          <p className="text-xs font-mono uppercase tracking-wide text-muted mb-4">Cost by backend</p>
          {cost && cost.breakdown.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={cost.breakdown}>
                <XAxis dataKey="backend" tick={{ fill: "#7C8699", fontSize: 11 }} axisLine={{ stroke: "#232938" }} />
                <YAxis tick={{ fill: "#7C8699", fontSize: 11 }} axisLine={{ stroke: "#232938" }} />
                <Tooltip
                  contentStyle={{ background: "#131720", border: "1px solid #232938", fontSize: 12 }}
                  labelStyle={{ color: "#E4E7EB" }}
                />
                <Bar dataKey="cost" radius={[4, 4, 0, 0]}>
                  {cost.breakdown.map((d) => (
                    <Cell key={d.backend} fill={COLOR_HEX[d.backend] || "#7C8699"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-muted py-16 text-center">No cost data yet</p>
          )}
        </div>
      </div>
    </div>
  );
}

function KpiCard({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="border border-border rounded-md bg-surface p-4">
      <p className="text-xs font-mono uppercase tracking-wide text-muted mb-1">{label}</p>
      <p className={`text-2xl font-mono font-semibold ${accent || "text-ink"}`}>{value}</p>
    </div>
  );
}
