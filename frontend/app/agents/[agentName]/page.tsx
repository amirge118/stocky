"use client"

import { useEffect, useRef, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { ArrowLeft, Loader2, Play } from "lucide-react"
import { timeAgo, fmtDate } from "@/lib/utils/time"
import { listAgents, getLatestReport, getAgentHistory, triggerAgent } from "@/lib/api/agents"
import { AgentReportView } from "@/components/features/agents/AgentReportView"
import { Button } from "@/components/ui/button"

export default function AgentDetailPage() {
  const params = useParams()
  const agentName = params.agentName as string
  const router = useRouter()
  const queryClient = useQueryClient()
  const [triggering, setTriggering] = useState(false)
  const [symbol, setSymbol] = useState("")
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [])

  const { data: agentList } = useQuery({
    queryKey: ["agents"],
    queryFn: listAgents,
    staleTime: 5 * 60_000,
  })

  const meta = agentList?.agents.find((a) => a.name === agentName)

  const { data: latest, isPending: latestPending } = useQuery({
    queryKey: ["agent-report", agentName, symbol || undefined],
    queryFn: () => getLatestReport(agentName, symbol || undefined),
    staleTime: 60 * 60_000,
    retry: 1,
  })

  const { data: history } = useQuery({
    queryKey: ["agent-history", agentName],
    queryFn: () => getAgentHistory(agentName),
    staleTime: 5 * 60_000,
    retry: 1,
  })

  async function handleTrigger() {
    setTriggering(true)
    try {
      await triggerAgent(agentName, symbol ? { symbol } : undefined)
      timerRef.current = setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["agent-report", agentName] })
        queryClient.invalidateQueries({ queryKey: ["agent-history", agentName] })
        setTriggering(false)
      }, 5000)
    } catch {
      setTriggering(false)
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        {/* Back */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1.5 text-zinc-400 hover:text-zinc-200 text-sm transition-colors"
        >
          <ArrowLeft size={15} />
          Back
        </button>

        {/* Header */}
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500 mb-1">
              {meta?.agent_type ?? "Agent"}
            </p>
            <h1 className="text-2xl font-bold">{agentName.replace(/_/g, " ")}</h1>
            {meta?.description && (
              <p className="text-sm text-zinc-500 mt-1">{meta.description}</p>
            )}
            {meta?.schedule_cron && (
              <p className="text-xs text-zinc-600 mt-1">
                Scheduled: <code className="font-mono">{meta.schedule_cron}</code>
              </p>
            )}
          </div>

          <div className="flex items-center gap-2">
            {meta?.agent_type === "stock" && (
              <input
                type="text"
                placeholder="Symbol (e.g. AAPL)"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="h-8 px-3 text-sm bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder:text-zinc-600 focus:outline-none focus:border-zinc-500 w-36"
              />
            )}
            <Button
              size="sm"
              disabled={triggering || (meta?.agent_type === "stock" && !symbol)}
              onClick={handleTrigger}
              className="h-8 px-3 text-xs bg-indigo-600 hover:bg-indigo-500 gap-1.5"
            >
              {triggering ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <Play size={12} />
              )}
              {triggering ? "Running…" : "Run Now"}
            </Button>
          </div>
        </div>

        {/* Latest report */}
        <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-5">
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide mb-4">
            Latest Report
            {latest?.created_at && (
              <span className="ml-2 text-zinc-600 normal-case font-normal">
                · {timeAgo(latest.created_at)}
              </span>
            )}
          </h2>

          {latestPending ? (
            <div className="space-y-2 animate-pulse">
              <div className="h-3 bg-zinc-800 rounded w-1/3" />
              <div className="h-3 bg-zinc-800 rounded w-full" />
              <div className="h-3 bg-zinc-800 rounded w-5/6" />
            </div>
          ) : latest ? (
            <AgentReportView report={latest} />
          ) : (
            <p className="text-sm text-zinc-500">No report yet. Click Run Now to generate one.</p>
          )}
        </div>

        {/* History */}
        {history && history.length > 0 && (
          <div>
            <h2 className="text-sm font-semibold text-zinc-500 uppercase tracking-wide mb-3">
              History
            </h2>
            <div className="space-y-2">
              {history.map((run) => (
                <div
                  key={run.id}
                  className="flex items-center gap-4 text-xs bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5"
                >
                  <span
                    className={`w-2 h-2 rounded-full shrink-0 ${
                      run.status === "completed"
                        ? "bg-green-500"
                        : run.status === "failed"
                          ? "bg-red-500"
                          : "bg-zinc-500"
                    }`}
                  />
                  <span className="text-zinc-400 font-mono">
                    {fmtDate(run.created_at)}
                  </span>
                  {run.target_symbol && (
                    <span className="text-zinc-500">{run.target_symbol}</span>
                  )}
                  <span
                    className={
                      run.status === "completed"
                        ? "text-green-400"
                        : run.status === "failed"
                          ? "text-red-400"
                          : "text-zinc-500"
                    }
                  >
                    {run.status}
                  </span>
                  {run.run_duration_ms && (
                    <span className="text-zinc-600 ml-auto">{run.run_duration_ms}ms</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
