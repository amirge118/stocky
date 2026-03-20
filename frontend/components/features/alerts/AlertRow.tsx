"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { deleteAlert, updateAlert } from "@/lib/api/alerts"
import type { Alert } from "@/types/alerts"

const CONDITION_LABEL: Record<string, string> = {
  ABOVE: "Above",
  BELOW: "Below",
  EQUAL: "Equal",
}

const CONDITION_CLASS: Record<string, string> = {
  ABOVE: "bg-green-900/40 text-green-400 border border-green-700/50",
  BELOW: "bg-red-900/40 text-red-400 border border-red-700/50",
  EQUAL: "bg-blue-900/40 text-blue-400 border border-blue-700/50",
}

function relativeTime(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime()
  const minutes = Math.floor(diff / 60_000)
  if (minutes < 1) return "just now"
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

interface AlertRowProps {
  alert: Alert
  showTicker?: boolean
}

export function AlertRow({ alert, showTicker = true }: AlertRowProps) {
  const queryClient = useQueryClient()

  const toggleMutation = useMutation({
    mutationFn: () => updateAlert(alert.id, { is_active: !alert.is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] })
      queryClient.invalidateQueries({ queryKey: ["alerts", alert.ticker] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteAlert(alert.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] })
      queryClient.invalidateQueries({ queryKey: ["alerts", alert.ticker] })
    },
  })

  return (
    <div className="flex items-center gap-4 px-4 py-3 rounded-lg bg-zinc-900/50 hover:bg-zinc-800/60 transition-colors">
      {/* Ticker */}
      {showTicker && (
        <span className="font-mono font-semibold text-sm text-zinc-100 border border-zinc-700 rounded px-1.5 py-0.5 shrink-0">
          {alert.ticker}
        </span>
      )}

      {/* Condition chip */}
      <span
        className={`text-xs font-medium rounded px-2 py-0.5 shrink-0 ${CONDITION_CLASS[alert.condition_type] ?? ""}`}
      >
        {CONDITION_LABEL[alert.condition_type] ?? alert.condition_type}
      </span>

      {/* Target price */}
      <span className="font-mono text-sm text-white tabular-nums shrink-0">
        ${parseFloat(alert.target_price).toFixed(2)}
      </span>

      {/* Last triggered */}
      <span className="text-xs text-zinc-500 flex-1 min-w-0 truncate">
        {alert.last_triggered
          ? `Triggered ${relativeTime(alert.last_triggered)}`
          : "Never triggered"}
      </span>

      {/* Toggle */}
      <button
        onClick={() => toggleMutation.mutate()}
        disabled={toggleMutation.isPending}
        title={alert.is_active ? "Deactivate" : "Activate"}
        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors shrink-0 focus:outline-none ${
          alert.is_active ? "bg-green-600" : "bg-zinc-700"
        } ${toggleMutation.isPending ? "opacity-50 cursor-not-allowed" : ""}`}
      >
        <span
          className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${
            alert.is_active ? "translate-x-4" : "translate-x-1"
          }`}
        />
      </button>

      {/* Delete */}
      <button
        onClick={() => deleteMutation.mutate()}
        disabled={deleteMutation.isPending}
        title="Delete alert"
        className="p-1.5 rounded text-zinc-600 hover:text-red-400 hover:bg-zinc-700 transition-colors text-xs shrink-0"
      >
        ✕
      </button>
    </div>
  )
}
