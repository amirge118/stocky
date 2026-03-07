"use client"

import { useEffect, useRef, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Loader2, Play, Zap } from "lucide-react"
import { getLatestReport, triggerAgent } from "@/lib/api/agents"
import { AgentReportView } from "./AgentReportView"
import { Button } from "@/components/ui/button"

interface StockDeepDiveCardProps {
  symbol: string
}

export function StockDeepDiveCard({ symbol }: StockDeepDiveCardProps) {
  const [triggering, setTriggering] = useState(false)
  const queryClient = useQueryClient()
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [])

  const { data: report, isPending } = useQuery({
    queryKey: ["agent-report", "stock_deep_dive", symbol],
    queryFn: () => getLatestReport("stock_deep_dive", symbol),
    staleTime: 60 * 60_000, // 1 hour
    retry: 1,
  })

  async function handleTrigger() {
    setTriggering(true)
    try {
      await triggerAgent("stock_deep_dive", { symbol })
      timerRef.current = setTimeout(() => {
        queryClient.invalidateQueries({
          queryKey: ["agent-report", "stock_deep_dive", symbol],
        })
        setTriggering(false)
      }, 5000)
    } catch {
      setTriggering(false)
    }
  }

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 border-l-4 border-l-indigo-500 p-5">
      <div className="flex items-center justify-between gap-2 mb-4">
        <div className="flex items-center gap-2">
          <Zap size={14} className="text-indigo-400" />
          <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wide">
            Deep Dive Analysis
          </h2>
          <span className="text-xs text-zinc-600 ml-1">AI Agent</span>
        </div>
        <Button
          size="sm"
          variant="outline"
          disabled={triggering}
          onClick={handleTrigger}
          className="h-7 px-2.5 text-xs border-zinc-700 text-zinc-400 hover:bg-zinc-800 gap-1"
        >
          {triggering ? (
            <Loader2 size={11} className="animate-spin" />
          ) : (
            <Play size={11} />
          )}
          {triggering ? "Running…" : "Run"}
        </Button>
      </div>

      {isPending ? (
        <div className="space-y-2 animate-pulse">
          <div className="h-3 bg-zinc-800 rounded w-1/3" />
          <div className="h-3 bg-zinc-800 rounded w-full" />
          <div className="h-3 bg-zinc-800 rounded w-5/6" />
        </div>
      ) : report ? (
        <AgentReportView report={report} />
      ) : (
        <p className="text-sm text-zinc-500">
          No analysis yet. Click <span className="text-zinc-300 font-medium">Run</span> to generate a deep-dive.
        </p>
      )}
    </div>
  )
}
