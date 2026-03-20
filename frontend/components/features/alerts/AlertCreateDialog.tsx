"use client"

import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { createAlert } from "@/lib/api/alerts"
import type { ConditionType } from "@/types/alerts"
import { NotificationChannelHint } from "./NotificationChannelHint"

const CONDITIONS: { value: ConditionType; label: string }[] = [
  { value: "ABOVE", label: "Above" },
  { value: "BELOW", label: "Below" },
  { value: "EQUAL", label: "Equal" },
]

interface AlertCreateDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function AlertCreateDialog({ open, onOpenChange }: AlertCreateDialogProps) {
  const queryClient = useQueryClient()
  const [ticker, setTicker] = useState("")
  const [condition, setCondition] = useState<ConditionType>("ABOVE")
  const [price, setPrice] = useState("")
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: () =>
      createAlert({
        ticker: ticker.trim().toUpperCase(),
        condition_type: condition,
        target_price: parseFloat(price),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] })
      onOpenChange(false)
      setTicker("")
      setCondition("ABOVE")
      setPrice("")
      setError(null)
    },
    onError: (err: Error) => {
      setError(err.message || "Failed to create alert")
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!ticker.trim()) { setError("Ticker is required"); return }
    const p = parseFloat(price)
    if (isNaN(p) || p <= 0) { setError("Target price must be a positive number"); return }
    mutation.mutate()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[440px] bg-zinc-900 border-zinc-700">
        <DialogHeader>
          <DialogTitle className="text-white">New Price Alert</DialogTitle>
        </DialogHeader>

        <NotificationChannelHint />

        <form onSubmit={handleSubmit} className="space-y-4 pt-1" noValidate>
          <div className="space-y-1">
            <label className="text-xs text-zinc-400 font-medium">Ticker</label>
            <Input
              autoFocus
              placeholder="e.g. AAPL"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              maxLength={10}
              className="bg-zinc-800 border-zinc-600 text-white placeholder:text-zinc-500 focus-visible:ring-zinc-500 font-mono uppercase"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs text-zinc-400 font-medium">Condition</label>
            <div className="flex gap-2">
              {CONDITIONS.map(({ value, label }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setCondition(value)}
                  className={`flex-1 py-2 rounded text-sm font-medium transition-colors ${
                    condition === value
                      ? value === "ABOVE"
                        ? "bg-green-700 text-white"
                        : value === "BELOW"
                          ? "bg-red-700 text-white"
                          : "bg-blue-700 text-white"
                      : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs text-zinc-400 font-medium">Target Price ($)</label>
            <Input
              type="number"
              placeholder="0.00"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              min={0.0001}
              step="any"
              className="bg-zinc-800 border-zinc-600 text-white placeholder:text-zinc-500 focus-visible:ring-zinc-500"
            />
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <div className="flex justify-end gap-2 pt-1">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="border-zinc-600 text-zinc-300 hover:bg-zinc-800 hover:text-white"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={mutation.isPending}
              className="bg-zinc-100 text-zinc-900 hover:bg-white"
            >
              {mutation.isPending ? "Creating…" : "Create Alert"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
