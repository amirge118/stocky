"use client"

import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Bell } from "lucide-react"
import { useAlerts } from "@/lib/hooks/useAlerts"
import { NotificationChannelHint } from "@/components/features/alerts/NotificationChannelHint"

export interface AlertDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  symbol?: string
  currentPrice?: number
}

type Mode = "price" | "percent"

export function AlertDialog({ open, onOpenChange, symbol: initialSymbol, currentPrice }: AlertDialogProps) {
  const { addAlert } = useAlerts()
  const [symbol, setSymbol] = useState(initialSymbol?.toUpperCase() ?? "")
  const [mode, setMode] = useState<Mode>("price")
  const [direction, setDirection] = useState<"above" | "below">("above")
  const [priceInput, setPriceInput] = useState("")
  const [percentInput, setPercentInput] = useState("")

  function computedTargetPrice(): number | null {
    if (mode === "price") {
      const v = parseFloat(priceInput)
      return isNaN(v) || v <= 0 ? null : v
    }
    const pct = parseFloat(percentInput)
    if (isNaN(pct) || pct <= 0 || !currentPrice) return null
    return direction === "above"
      ? currentPrice * (1 + pct / 100)
      : currentPrice * (1 - pct / 100)
  }

  const targetPrice = computedTargetPrice()
  const pctVal = parseFloat(percentInput)
  const canSubmit = (initialSymbol || symbol.trim()) && targetPrice !== null

  const handleSubmit = () => {
    if (!canSubmit || targetPrice === null) return
    const ticker = (initialSymbol || symbol.trim()).toUpperCase()
    addAlert(ticker, parseFloat(targetPrice.toFixed(2)), direction)
    setPriceInput("")
    setPercentInput("")
    if (!initialSymbol) setSymbol("")
    onOpenChange(false)
  }

  function switchMode(next: Mode) {
    setMode(next)
    if (next === "percent" && direction === "above") { /* keep */ }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[380px] bg-zinc-900 border-zinc-700">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Bell size={18} />
            Price Alert{initialSymbol ? ` — ${initialSymbol.toUpperCase()}` : ""}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <NotificationChannelHint />

          {/* Symbol — only when not pre-set */}
          {!initialSymbol && (
            <div className="space-y-1.5">
              <Label className="text-zinc-300">Symbol</Label>
              <Input
                placeholder="e.g. AAPL"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="bg-zinc-800 border-zinc-600 text-white font-mono"
              />
            </div>
          )}

          {/* Mode toggle */}
          <div className="space-y-1.5">
            <Label className="text-zinc-300">Alert type</Label>
            <div className="flex gap-1 p-0.5 bg-zinc-800 rounded-lg w-fit">
              {(["price", "percent"] as Mode[]).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => switchMode(m)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                    mode === m
                      ? "bg-zinc-600 text-white"
                      : "text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {m === "price" ? "Price ($)" : "% Change"}
                </button>
              ))}
            </div>
          </div>

          {/* Direction */}
          <div className="space-y-1.5">
            <Label className="text-zinc-300">Notify when price goes</Label>
            <div className="flex gap-2">
              {(mode === "price"
                ? [{ label: "Above", value: "above" }, { label: "Below", value: "below" }]
                : [{ label: "Up", value: "above" }, { label: "Down", value: "below" }]
              ).map(({ label, value }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setDirection(value as "above" | "below")}
                  className={`flex-1 py-2 text-sm font-medium rounded-lg border transition-colors ${
                    direction === value
                      ? value === "above"
                        ? "bg-green-700/40 border-green-600 text-green-300"
                        : "bg-red-700/40 border-red-600 text-red-300"
                      : "bg-zinc-800 border-zinc-700 text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Value input */}
          <div className="space-y-1.5">
            <Label className="text-zinc-300">
              {mode === "price" ? "Target price ($)" : "Change (%)"}
            </Label>
            <div className="relative flex items-center">
              <span className="absolute left-3 text-zinc-500 text-sm pointer-events-none">
                {mode === "price" ? "$" : "%"}
              </span>
              <Input
                type="number"
                min="0.01"
                step="any"
                placeholder={mode === "price" ? "150.00" : "5"}
                value={mode === "price" ? priceInput : percentInput}
                onChange={(e) =>
                  mode === "price"
                    ? setPriceInput(e.target.value)
                    : setPercentInput(e.target.value)
                }
                className="bg-zinc-800 border-zinc-600 text-white pl-8"
              />
            </div>
            {/* Helper for % mode */}
            {mode === "percent" && targetPrice !== null && !isNaN(pctVal) && currentPrice && (
              <p className="text-xs text-zinc-500">
                →{" "}
                <span className="font-mono text-zinc-300">${targetPrice.toFixed(2)}</span>{" "}
                ({pctVal}% {direction === "above" ? "above" : "below"} ${currentPrice.toFixed(2)})
              </p>
            )}
            {mode === "percent" && !currentPrice && (
              <p className="text-xs text-zinc-600">Live price unavailable — enter a fixed price instead.</p>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="border-zinc-600 text-zinc-300"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!canSubmit}
              className="bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-40"
            >
              Add Alert
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
