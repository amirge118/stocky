"use client"

import { useCallback, useRef, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import Link from "next/link"
import { Bot, ChevronRight } from "lucide-react"
import { listAgents, getLatestReport, triggerAgent } from "@/lib/api/agents"
import { AgentCard } from "@/components/features/agents/AgentCard"

export default function AgentsDashboardPage() {
  const queryClient = useQueryClient()
  const [triggering, setTriggering] = useState<Record<string, boolean>>({})
  const timersRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({})

  const { data, isPending } = useQuery({
    queryKey: ["agents"],
    queryFn: listAgents,
    staleTime: 5 * 60_000,
  })

  const agents = data?.agents ?? []

  const handleTrigger = useCallback(async (agentName: string) => {
    setTriggering((prev) => ({ ...prev, [agentName]: true }))
    try {
      await triggerAgent(agentName)
      if (timersRef.current[agentName]) clearTimeout(timersRef.current[agentName])
      timersRef.current[agentName] = setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["agent-report", agentName] })
        setTriggering((prev) => ({ ...prev, [agentName]: false }))
      }, 5000)
    } catch {
      setTriggering((prev) => ({ ...prev, [agentName]: false }))
    }
  }, [queryClient])

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        {/* Header */}
        <div>
          <p className="text-[11px] font-medium tracking-widest uppercase text-zinc-500 mb-1">
            Multi-Agent AI
          </p>
          <div className="flex items-center gap-2">
            <Bot size={22} className="text-indigo-400" />
            <h1 className="text-3xl font-bold tracking-tight">Agents</h1>
          </div>
          <p className="text-sm text-zinc-500 mt-1">
            Specialized AI agents that analyze stocks, portfolio health, market trends, and sectors.
          </p>
        </div>

        {/* Agent grid */}
        {isPending ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[...Array(4)].map((_, i) => (
              <div
                key={i}
                className="animate-pulse rounded-xl bg-zinc-900 border border-zinc-800 h-44"
              />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {agents.map((agent) => (
              <AgentCardWithData
                key={agent.name}
                agent={agent}
                isTriggering={!!triggering[agent.name]}
                onTrigger={() => handleTrigger(agent.name)}
              />
            ))}
          </div>
        )}

        {/* Link to individual agent pages */}
        {agents.length > 0 && (
          <div>
            <p className="text-xs text-zinc-600 mb-2">Agent details</p>
            <div className="flex flex-wrap gap-2">
              {agents.map((a) => (
                <Link
                  key={a.name}
                  href={`/agents/${a.name}`}
                  className="flex items-center gap-1 text-xs text-zinc-400 hover:text-zinc-200 transition-colors bg-zinc-800 hover:bg-zinc-700 px-3 py-1.5 rounded-lg"
                >
                  {a.name.replace(/_/g, " ")}
                  <ChevronRight size={11} />
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Sub-component to fetch per-agent report inside its own query
function AgentCardWithData({
  agent,
  isTriggering,
  onTrigger,
}: {
  agent: { name: string; agent_type: string; description: string; schedule_cron: string | null }
  isTriggering: boolean
  onTrigger: () => void
}) {
  const skip = agent.agent_type === "stock"

  const { data: report } = useQuery({
    queryKey: ["agent-report", agent.name],
    queryFn: () => getLatestReport(agent.name),
    staleTime: 60 * 60_000,
    retry: 1,
    enabled: !skip,
  })

  return (
    <AgentCard
      meta={agent}
      report={skip ? undefined : report}
      onTrigger={onTrigger}
      isTriggering={isTriggering}
    />
  )
}
