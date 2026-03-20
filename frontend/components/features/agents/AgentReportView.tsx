"use client"

import type { AgentReport } from "@/types/agent"

function Badge({
  value,
  colors,
}: {
  value: string
  colors: Record<string, string>
}) {
  const cls = colors[value] ?? "bg-zinc-800 text-zinc-400"
  return (
    <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${cls}`}>
      {value}
    </span>
  )
}

function StockDeepDiveView({ data }: { data: Record<string, unknown> }) {
  const recColors: Record<string, string> = {
    BUY: "bg-green-500/15 text-green-400",
    HOLD: "bg-amber-500/15 text-amber-400",
    SELL: "bg-red-500/15 text-red-400",
  }
  const sentColors: Record<string, string> = {
    POSITIVE: "bg-green-500/15 text-green-400",
    NEUTRAL: "bg-zinc-700 text-zinc-400",
    NEGATIVE: "bg-red-500/15 text-red-400",
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <Badge value={(data.recommendation as string) ?? "—"} colors={recColors} />
        <Badge value={(data.sentiment as string) ?? "—"} colors={sentColors} />
        <span className="text-xs text-zinc-500">
          Conviction: {(data.conviction as string) ?? "—"}
        </span>
        {data.price_target_12m !== null && data.price_target_12m !== undefined && (
          <span className="text-xs text-zinc-400">
            12M target: ${(data.price_target_12m as number).toFixed(2)}
          </span>
        )}
      </div>

      {data.summary ? (
        <p className="text-sm text-zinc-300 leading-relaxed">{String(data.summary)}</p>
      ) : null}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {data.bull_case ? (
          <div className="bg-green-500/5 border border-green-500/15 rounded-lg p-3">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-green-600 mb-1">
              Bull Case
            </p>
            <p className="text-xs text-zinc-300">{String(data.bull_case)}</p>
          </div>
        ) : null}
        {data.bear_case ? (
          <div className="bg-red-500/5 border border-red-500/15 rounded-lg p-3">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-red-600 mb-1">
              Bear Case
            </p>
            <p className="text-xs text-zinc-300">{String(data.bear_case)}</p>
          </div>
        ) : null}
      </div>

      {Array.isArray(data.key_risks) && data.key_risks.length > 0 && (
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500 mb-2">
            Key Risks
          </p>
          <ul className="space-y-1">
            {(data.key_risks as string[]).map((r) => (
              <li key={r} className="text-xs text-zinc-400 flex gap-2">
                <span className="text-zinc-600 shrink-0">·</span>
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function PortfolioHealthView({ data }: { data: Record<string, unknown> }) {
  const gradeColors: Record<string, string> = {
    A: "bg-green-500/15 text-green-400",
    B: "bg-green-500/15 text-green-400",
    C: "bg-amber-500/15 text-amber-400",
    D: "bg-orange-500/15 text-orange-400",
    F: "bg-red-500/15 text-red-400",
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 flex-wrap">
        <div>
          <p className="text-[10px] text-zinc-500 uppercase tracking-widest">Risk Score</p>
          <p className="text-2xl font-bold text-white">{data.risk_score as number}/10</p>
        </div>
        <div>
          <p className="text-[10px] text-zinc-500 uppercase tracking-widest">Grade</p>
          <Badge
            value={(data.diversification_grade as string) ?? "—"}
            colors={gradeColors}
          />
        </div>
        {data.hhi_index !== undefined && (
          <div>
            <p className="text-[10px] text-zinc-500 uppercase tracking-widest">HHI</p>
            <p className="text-sm font-semibold text-zinc-300">
              {(data.hhi_index as number).toFixed(3)}
            </p>
          </div>
        )}
      </div>

      {data.summary ? (
        <p className="text-sm text-zinc-300 leading-relaxed">{String(data.summary)}</p>
      ) : null}

      {Array.isArray(data.top_concerns) && data.top_concerns.length > 0 && (
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500 mb-2">
            Top Concerns
          </p>
          <ul className="space-y-1">
            {(data.top_concerns as string[]).map((c) => (
              <li key={c} className="text-xs text-zinc-400 flex gap-2">
                <span className="text-zinc-600 shrink-0">·</span>
                {c}
              </li>
            ))}
          </ul>
        </div>
      )}

      {Array.isArray(data.rebalancing_suggestions) &&
        data.rebalancing_suggestions.length > 0 && (
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500 mb-2">
              Rebalancing Suggestions
            </p>
            <ul className="space-y-1">
              {(data.rebalancing_suggestions as string[]).map((s) => (
                <li key={s} className="text-xs text-zinc-400 flex gap-2">
                  <span className="text-green-600 shrink-0">→</span>
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}
    </div>
  )
}

function MarketScannerView({ data }: { data: Record<string, unknown> }) {
  const moodColors: Record<string, string> = {
    BULLISH: "bg-green-500/15 text-green-400",
    BEARISH: "bg-red-500/15 text-red-400",
    NEUTRAL: "bg-zinc-700 text-zinc-400",
    MIXED: "bg-amber-500/15 text-amber-400",
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Badge value={(data.market_mood as string) ?? "—"} colors={moodColors} />
        {data.stocks_scanned !== undefined && (
          <span className="text-xs text-zinc-500">
            {data.stocks_scanned as number} stocks scanned
          </span>
        )}
      </div>

      {data.summary ? (
        <p className="text-sm text-zinc-300 leading-relaxed">{String(data.summary)}</p>
      ) : null}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {Array.isArray(data.top_opportunities) && data.top_opportunities.length > 0 && (
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-green-600 mb-2">
              Opportunities
            </p>
            <ul className="space-y-1">
              {(data.top_opportunities as string[]).map((o) => (
                <li key={o} className="text-xs text-zinc-300 flex gap-2">
                  <span className="text-green-600 shrink-0">↑</span>
                  {o}
                </li>
              ))}
            </ul>
          </div>
        )}
        {Array.isArray(data.top_risks) && data.top_risks.length > 0 && (
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-red-600 mb-2">
              Risks
            </p>
            <ul className="space-y-1">
              {(data.top_risks as string[]).map((r) => (
                <li key={r} className="text-xs text-zinc-300 flex gap-2">
                  <span className="text-red-600 shrink-0">↓</span>
                  {r}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

function SectorTrendView({ data }: { data: Record<string, unknown> }) {
  const trendColors: Record<string, string> = {
    UPTREND: "bg-green-500/15 text-green-400",
    DOWNTREND: "bg-red-500/15 text-red-400",
    SIDEWAYS: "bg-zinc-700 text-zinc-400",
  }
  const outlookColors: Record<string, string> = {
    POSITIVE: "bg-green-500/15 text-green-400",
    NEUTRAL: "bg-zinc-700 text-zinc-400",
    NEGATIVE: "bg-red-500/15 text-red-400",
  }

  const sectors = Array.isArray(data.sectors)
    ? (data.sectors as Array<Record<string, unknown>>)
    : []

  return (
    <div className="space-y-4">
      {data.summary ? (
        <p className="text-sm text-zinc-300 leading-relaxed">{String(data.summary)}</p>
      ) : null}

      <div className="flex gap-4 flex-wrap text-xs text-zinc-500">
        {data.best_sector ? (
          <span>
            Best: <span className="text-green-400">{String(data.best_sector)}</span>
          </span>
        ) : null}
        {data.worst_sector ? (
          <span>
            Worst: <span className="text-red-400">{String(data.worst_sector)}</span>
          </span>
        ) : null}
      </div>

      {sectors.length > 0 && (
        <div className="space-y-2">
          {sectors.map((s, i) => (
            <div
              key={i}
              className="flex items-center gap-3 justify-between bg-zinc-800/40 rounded-lg px-3 py-2"
            >
              <span className="text-xs text-zinc-300 font-medium w-36 shrink-0">
                {s.sector as string}
              </span>
              <div className="flex items-center gap-2 flex-wrap">
                <Badge
                  value={(s.trend_direction as string) ?? "—"}
                  colors={trendColors}
                />
                <Badge
                  value={(s.outlook_12m as string) ?? "—"}
                  colors={outlookColors}
                />
                {s.performance_3m !== null && s.performance_3m !== undefined && (
                  <span
                    className={`text-xs ${(s.performance_3m as number) >= 0 ? "text-green-400" : "text-red-400"}`}
                  >
                    3M: {(s.performance_3m as number) >= 0 ? "+" : ""}
                    {(s.performance_3m as number).toFixed(1)}%
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

interface AgentReportViewProps {
  report: AgentReport
}

export function AgentReportView({ report }: AgentReportViewProps) {
  if (report.status === "failed") {
    return (
      <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-4">
        <p className="font-semibold mb-1">Agent failed</p>
        <p className="text-xs text-red-300/70">{report.error_message}</p>
      </div>
    )
  }

  if (!report.data) {
    return <p className="text-sm text-zinc-500">No data available.</p>
  }

  const data = report.data

  if (report.agent_type === "stock") return <StockDeepDiveView data={data} />
  if (report.agent_type === "portfolio") return <PortfolioHealthView data={data} />
  if (report.agent_type === "market") return <MarketScannerView data={data} />
  if (report.agent_type === "sector") return <SectorTrendView data={data} />

  return (
    <pre className="text-xs text-zinc-400 overflow-auto max-h-64 bg-zinc-800/50 rounded-lg p-3">
      {JSON.stringify(data, null, 2)}
    </pre>
  )
}
