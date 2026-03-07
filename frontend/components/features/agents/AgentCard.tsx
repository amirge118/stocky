"use client"

import { Play, Clock, CheckCircle, XCircle, Loader2 } from "lucide-react"
import { timeAgo } from "@/lib/utils/time"
import type { AgentMeta, AgentReport } from "@/types/agent"
import { Button } from "@/components/ui/button"

const TYPE_COLORS: Record<string, string> = {
  stock: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
  portfolio: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  market: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  sector: "bg-violet-500/10 text-violet-400 border-violet-500/20",
}

const STATUS_ICON = {
  completed: <CheckCircle size={13} className="text-emerald-400" />,
  failed: <XCircle size={13} className="text-red-400" />,
  running: <Loader2 size={13} className="text-blue-400 animate-spin" />,
  pending: <Clock size={13} className="text-zinc-500" />,
}

interface AgentCardProps {
  meta: AgentMeta
  report: AgentReport | null | undefined
  onTrigger: () => void
  isTriggering: boolean
  symbol?: string
}

export function AgentCard({
  meta,
  report,
  onTrigger,
  isTriggering,
  symbol,
}: AgentCardProps) {
  const typeColor = TYPE_COLORS[meta.agent_type] ?? "bg-zinc-800 text-zinc-400"
  const statusIcon = report ? STATUS_ICON[report.status] ?? null : null
  const lastRun = report?.created_at ? timeAgo(report.created_at) : null

  // Quick preview of key data fields
  const preview = (() => {
    if (!report?.data) return null
    const d = report.data
    if (meta.agent_type === "stock" && d.recommendation)
      return `${d.recommendation as string} · ${d.conviction as string}`
    if (meta.agent_type === "portfolio" && d.risk_score !== undefined)
      return `Risk ${d.risk_score as number}/10 · Grade ${d.diversification_grade as string}`
    if (meta.agent_type === "market" && d.market_mood)
      return `Mood: ${d.market_mood as string}`
    if (meta.agent_type === "sector" && d.best_sector)
      return `Best: ${d.best_sector as string}`
    return null
  })()

  const canTrigger = meta.agent_type !== "stock" || Boolean(symbol)

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-5 flex flex-col gap-4 hover:border-zinc-700 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`text-[10px] font-semibold uppercase tracking-widest px-2 py-0.5 rounded border ${typeColor}`}
            >
              {meta.agent_type}
            </span>
            {meta.schedule_cron ? (
              <span className="text-[10px] text-zinc-600 flex items-center gap-1">
                <Clock size={10} />
                Scheduled
              </span>
            ) : (
              <span className="text-[10px] text-zinc-600">On-demand</span>
            )}
          </div>
          <h3 className="text-sm font-semibold text-white">{meta.name.replace(/_/g, " ")}</h3>
          <p className="text-xs text-zinc-500 mt-0.5 leading-relaxed">{meta.description}</p>
        </div>
      </div>

      {/* Last run info */}
      <div className="flex items-center gap-2 text-xs text-zinc-600">
        {statusIcon}
        {lastRun ? (
          <>
            <span>Last run {lastRun}</span>
            {report?.run_duration_ms && (
              <span className="text-zinc-700">· {report.run_duration_ms}ms</span>
            )}
          </>
        ) : (
          <span>Never run</span>
        )}
      </div>

      {/* Preview */}
      {preview && (
        <div className="text-xs text-zinc-400 bg-zinc-800/60 rounded-lg px-3 py-2">
          {preview}
        </div>
      )}

      {/* Trigger button */}
      <Button
        size="sm"
        variant="outline"
        disabled={isTriggering || !canTrigger}
        onClick={onTrigger}
        className="h-7 px-3 text-xs border-zinc-700 text-zinc-300 hover:bg-zinc-800 gap-1.5 self-start"
      >
        {isTriggering ? (
          <Loader2 size={11} className="animate-spin" />
        ) : (
          <Play size={11} />
        )}
        {isTriggering ? "Running…" : "Run Now"}
      </Button>
    </div>
  )
}
