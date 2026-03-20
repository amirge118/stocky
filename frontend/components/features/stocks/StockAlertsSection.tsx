"use client"

import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createAlert, fetchAlerts } from "@/lib/api/alerts"
import { AlertRow } from "@/components/features/alerts/AlertRow"
import { NotificationChannelHint } from "@/components/features/alerts/NotificationChannelHint"
import type { ConditionType } from "@/types/alerts"

type Mode = "price" | "percent"

interface Props {
  symbol: string
  currentPrice?: number
}

export function StockAlertsSection({ symbol, currentPrice }: Props) {
  const queryClient = useQueryClient()

  const [mode, setMode] = useState<Mode>("price")
  const [condition, setCondition] = useState<ConditionType>("ABOVE")
  const [priceInput, setPriceInput] = useState("")
  const [percentInput, setPercentInput] = useState("")

  const { data: alerts, isLoading } = useQuery({
    queryKey: ["alerts", symbol],
    queryFn: () => fetchAlerts(50, 0, symbol),
    refetchInterval: 60_000,
  })

  const mutation = useMutation({
    mutationFn: createAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] })
      queryClient.invalidateQueries({ queryKey: ["alerts", symbol] })
      setPriceInput("")
      setPercentInput("")
    },
  })

  function computedTargetPrice(): number | null {
    if (mode === "price") {
      const v = parseFloat(priceInput)
      return isNaN(v) || v <= 0 ? null : v
    }
    const pct = parseFloat(percentInput)
    if (isNaN(pct) || pct <= 0 || !currentPrice) return null
    return condition === "ABOVE"
      ? currentPrice * (1 + pct / 100)
      : currentPrice * (1 - pct / 100)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const target = computedTargetPrice()
    if (target === null) return
    mutation.mutate({
      ticker: symbol.toUpperCase(),
      condition_type: condition,
      target_price: parseFloat(target.toFixed(2)),
    })
  }

  function switchMode(next: Mode) {
    setMode(next)
    if (next === "percent" && condition === "EQUAL") setCondition("ABOVE")
  }

  const targetPrice = computedTargetPrice()
  const percentVal = parseFloat(percentInput)

  const conditions =
    mode === "price"
      ? [
          { label: "↑", value: "ABOVE" as ConditionType },
          { label: "↓", value: "BELOW" as ConditionType },
          { label: "=", value: "EQUAL" as ConditionType },
        ]
      : [
          { label: "↑", value: "ABOVE" as ConditionType },
          { label: "↓", value: "BELOW" as ConditionType },
        ]

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-4 space-y-3">

      {/* Title row + mode toggle */}
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">
          Price Alerts
        </h2>
        <div className="flex gap-0.5 p-0.5 bg-zinc-800 rounded-lg">
          {(["price", "percent"] as Mode[]).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => switchMode(m)}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                mode === m
                  ? "bg-zinc-600 text-white shadow-sm"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {m === "price" ? "Price $" : "% Change"}
            </button>
          ))}
        </div>
      </div>

      <NotificationChannelHint />

      {/* Single-line form */}
      <form onSubmit={handleSubmit} className="space-y-1.5">
        <div className="flex items-center gap-1.5">
          {/* Condition pills */}
          {conditions.map(({ label, value }) => (
            <button
              key={value}
              type="button"
              onClick={() => setCondition(value)}
              className={`w-8 h-8 text-sm font-bold rounded-lg transition-colors shrink-0 flex items-center justify-center ${
                condition === value
                  ? value === "ABOVE"
                    ? "bg-green-600 text-white"
                    : value === "BELOW"
                    ? "bg-red-600 text-white"
                    : "bg-blue-600 text-white"
                  : "bg-zinc-800 text-zinc-400 hover:text-zinc-200 border border-zinc-700"
              }`}
            >
              {label}
            </button>
          ))}

          {/* Input */}
          <div className="relative flex-1 min-w-0">
            <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500 text-xs pointer-events-none">
              {mode === "price" ? "$" : "%"}
            </span>
            <input
              type="number"
              min="0"
              step="any"
              value={mode === "price" ? priceInput : percentInput}
              onChange={(e) =>
                mode === "price"
                  ? setPriceInput(e.target.value)
                  : setPercentInput(e.target.value)
              }
              placeholder={mode === "price" ? "0.00" : "5"}
              className="w-full pl-6 pr-2 py-1.5 text-sm bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 caret-white placeholder-zinc-600 focus:outline-none focus:border-zinc-500 [color-scheme:dark]"
            />
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={mutation.isPending || targetPrice === null}
            className="px-3 py-1.5 text-xs font-semibold bg-zinc-700 hover:bg-zinc-600 disabled:opacity-30 disabled:cursor-not-allowed text-white rounded-lg transition-colors shrink-0 border border-zinc-600"
          >
            {mutation.isPending ? "…" : "Add"}
          </button>
        </div>

        {/* Helper text */}
        {mode === "percent" && targetPrice !== null && !isNaN(percentVal) && currentPrice && (
          <p className="text-xs text-zinc-600 pl-0.5">
            → <span className="text-zinc-400 font-mono">${targetPrice.toFixed(2)}</span>
            {" "}({percentVal}% {condition === "ABOVE" ? "above" : "below"} ${currentPrice.toFixed(2)})
          </p>
        )}

        {mutation.isError && (
          <p className="text-xs text-red-400">Failed to create alert.</p>
        )}
      </form>

      {/* Alert list */}
      <div className="space-y-1">
        {isLoading ? (
          <>
            <div className="h-9 rounded-lg bg-zinc-800 animate-pulse" />
            <div className="h-9 rounded-lg bg-zinc-800 animate-pulse" />
          </>
        ) : alerts && alerts.length > 0 ? (
          alerts.map((alert) => <AlertRow key={alert.id} alert={alert} showTicker={false} />)
        ) : (
          <p className="text-xs text-zinc-600 pt-1">
            No alerts for {symbol.toUpperCase()} yet.
          </p>
        )}
      </div>
    </div>
  )
}
