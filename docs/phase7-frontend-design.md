# Phase 7 — Frontend Design
## Enterprise AI Gateway: Hybrid Token-Efficient Routing Agent

---

## 1. Screen List
1. **Login** — org admin/user auth.
2. **Dashboard (Overview)** — cost, tokens, routing distribution at a glance.
3. **Live Traffic / Traces** — recent requests with routing explainability drill-down.
4. **Trace Detail** — single trace's full decision breakdown.
5. **Analytics — Cost** — cost over time, per-backend breakdown, budget progress.
6. **Analytics — Tokens** — token usage over time.
7. **Policy Settings** — routing weights, privacy policy, budget threshold.
8. **API Keys** — create/revoke keys.
9. **Playground** — send a test prompt, see routing decision live (great demo screen).

## 2. Dashboard Design (Overview)
Top row: 4 KPI cards — Total Cost (30d), Total Requests, Cache Hit Rate, Avg Latency. Middle: routing distribution donut chart (share per backend) + cost-over-time line chart. Bottom: recent traces table (last 10) linking to Trace Detail.

## 3. Navigation
Left sidebar: Dashboard, Live Traffic, Analytics (Cost/Tokens submenu), Playground, Policy Settings, API Keys. Top bar: org switcher (platform_admin only), user menu.

## 4. Wireframes (textual)

```
+----------------------------------------------------+
| Logo   [Org: Acme Inc ▾]                [User ▾]    |
+---------+--------------------------------------------+
| Sidebar | KPI Cards: Cost | Requests | Cache% | Lat  |
| Dashboard|--------------------------------------------|
| Traffic | [Routing Donut]      [Cost Over Time Line]  |
| Analytics|--------------------------------------------|
| Playground| Recent Traces Table                       |
| Policy  | id | intent | backend | cost | time | →     |
| API Keys|--------------------------------------------|
+---------+--------------------------------------------+
```

**Playground screen:**
```
+----------------------------------------------------+
| Prompt input [textarea]      [Send]                 |
| Force backend: [auto ▾]                              |
+----------------------------------------------------+
| Response panel                                       |
| Routing explanation panel:                            |
|   intent: code | complexity: 0.72 | risk: none        |
|   scores: gemma .51 claude .88 gpt .83 gemini .79      |
|   chosen: claude — "highest quality-confidence..."     |
+----------------------------------------------------+
```

## 5. Component Tree

```
App
├── AuthProvider
├── Layout
│   ├── Sidebar
│   ├── Topbar (OrgSwitcher, UserMenu)
│   └── PageContainer
├── Pages/
│   ├── LoginPage
│   ├── DashboardPage
│   │   ├── KpiCard (x4)
│   │   ├── RoutingDonutChart
│   │   ├── CostOverTimeChart
│   │   └── RecentTracesTable
│   ├── LiveTrafficPage
│   │   └── TraceTable (paginated, filterable)
│   ├── TraceDetailPage
│   │   ├── ScoreBreakdown
│   │   └── ReasonPanel
│   ├── AnalyticsCostPage / AnalyticsTokensPage
│   │   ├── DateRangePicker
│   │   ├── BreakdownChart
│   │   └── BudgetProgressBar
│   ├── PolicySettingsPage
│   │   ├── WeightSliders (quality/cost/latency/budget)
│   │   └── PrivacyPolicySelect
│   ├── ApiKeysPage
│   │   └── ApiKeyTable + CreateKeyModal
│   └── PlaygroundPage
│       ├── PromptForm
│       ├── ResponsePanel
│       └── ExplanationPanel
└── shared/
    ├── Charts (recharts wrappers)
    ├── Table
    └── ApiClient (typed fetch wrapper over gateway REST API)
```

## 6. State Management
React Query (server state: traces, analytics, keys) + lightweight Context for auth/session; no heavy global store needed at this scope — avoids over-engineering for a hackathon timeline.

## 7. Responsive Strategy
Tailwind breakpoints; sidebar collapses to a hamburger drawer under `md`; charts stack vertically below `lg`; tables become horizontally scrollable on small screens.

## 8. Accessibility
Semantic HTML, ARIA labels on charts (with a text-table fallback), color-blind-safe palette for backend series (avoid pure red/green pairing), full keyboard navigation on forms/tables, visible focus states.

## 9. UI Guidelines
Design tokens and styling approach follow the `frontend-design` skill conventions — intentional typography, consistent spacing scale, one accent color per backend series used consistently across every chart (e.g., Gemma=teal, Claude=coral, GPT=indigo, Gemini=amber) so users learn the mapping instantly across screens.

---

**Next:** Phase 8 — Project Structure.
