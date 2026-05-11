"use client"

import { useState, useEffect } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { sellHolding } from "@/lib/api/portfolio"
import { useToast } from "@/hooks/use-toast"
import type { PortfolioPosition } from "@/types/portfolio"

interface Props {
  position: PortfolioPosition
  open: boolean
  onOpenChange: (open: boolean) => void
}

function fmtUSD(n: number): string {
  return n.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export function SellPositionDialog({ position, open, onOpenChange }: Props) {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const [sharesInput, setSharesInput] = useState("")
  const [priceInput, setPriceInput] = useState("")
  const [dateInput, setDateInput] = useState("")

  useEffect(() => {
    if (open) {
      setSharesInput("")
      setPriceInput(
        position.current_price != null ? position.current_price.toFixed(2) : ""
      )
      setDateInput(new Date().toISOString().split("T")[0])
    }
  }, [open, position.current_price])

  const sharesToSell = parseFloat(sharesInput)
  const pricePerShare = parseFloat(priceInput)

  const validShares =
    !Number.isNaN(sharesToSell) && sharesToSell > 0 && sharesToSell <= position.shares
  const validPrice = !Number.isNaN(pricePerShare) && pricePerShare > 0

  const estimatedProceeds =
    validShares && validPrice ? sharesToSell * pricePerShare : null
  const estimatedGain =
    validShares && validPrice
      ? (pricePerShare - position.avg_cost) * sharesToSell
      : null

  const mutation = useMutation({
    mutationFn: () =>
      sellHolding(position.symbol, {
        shares: sharesToSell,
        price_per_share: pricePerShare,
        transaction_date: dateInput || undefined,
      }),
    onSuccess: (result) => {
      if (result === null) {
        toast({ title: `Position closed`, description: `${position.symbol} fully sold` })
      } else {
        toast({
          title: `Sold ${sharesToSell} shares of ${position.symbol}`,
          description: estimatedGain != null
            ? `Realized gain: ${estimatedGain >= 0 ? "+" : ""}${fmtUSD(estimatedGain)}`
            : undefined,
        })
      }
      queryClient.invalidateQueries({ queryKey: ["portfolio-summary"] })
      queryClient.invalidateQueries({ queryKey: ["portfolio-news"] })
      onOpenChange(false)
    },
    onError: (err: Error) => {
      toast({ title: "Sell failed", description: err.message, variant: "destructive" })
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px] bg-zinc-900 border-zinc-700">
        <DialogHeader>
          <DialogTitle className="text-white">
            Sell {position.symbol}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-5">
          {/* Position summary */}
          <div className="rounded-lg bg-zinc-800 px-4 py-3 text-sm space-y-1">
            <div className="flex justify-between">
              <span className="text-zinc-400">Shares owned</span>
              <span className="text-white font-mono tabular-nums">
                {position.shares.toLocaleString("en-US")}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-400">Avg cost</span>
              <span className="text-white font-mono tabular-nums">
                {fmtUSD(position.avg_cost)}
              </span>
            </div>
            {position.current_price != null && (
              <div className="flex justify-between">
                <span className="text-zinc-400">Current price</span>
                <span className="text-white font-mono tabular-nums">
                  {fmtUSD(position.current_price)}
                </span>
              </div>
            )}
          </div>

          {/* Shares to sell */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label className="text-zinc-300">Shares to sell</Label>
              <button
                type="button"
                onClick={() => setSharesInput(String(position.shares))}
                className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                Sell All
              </button>
            </div>
            <Input
              type="number"
              min="0.001"
              max={position.shares}
              step="any"
              placeholder={`Max ${position.shares}`}
              value={sharesInput}
              onChange={(e) => setSharesInput(e.target.value)}
              className="bg-zinc-800 border-zinc-600 text-white placeholder:text-zinc-500 focus-visible:ring-zinc-500"
            />
          </div>

          {/* Sale price */}
          <div className="space-y-1.5">
            <Label className="text-zinc-300">Sale price per share ($)</Label>
            <Input
              type="number"
              min="0.01"
              step="any"
              placeholder="e.g. 180.00"
              value={priceInput}
              onChange={(e) => setPriceInput(e.target.value)}
              className="bg-zinc-800 border-zinc-600 text-white placeholder:text-zinc-500 focus-visible:ring-zinc-500"
            />
          </div>

          {/* Sale date */}
          <div className="space-y-1.5">
            <Label className="text-zinc-300">Sale date</Label>
            <Input
              type="date"
              max={new Date().toISOString().split("T")[0]}
              value={dateInput}
              onChange={(e) => setDateInput(e.target.value)}
              className="bg-zinc-800 border-zinc-600 text-white focus-visible:ring-zinc-500"
            />
          </div>

          {/* Live preview */}
          {estimatedProceeds != null && (
            <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 px-4 py-3 text-sm space-y-1">
              <div className="flex justify-between">
                <span className="text-zinc-400">Estimated proceeds</span>
                <span className="text-white font-mono tabular-nums">
                  {fmtUSD(estimatedProceeds)}
                </span>
              </div>
              {estimatedGain != null && (
                <div className="flex justify-between">
                  <span className="text-zinc-400">Estimated gain / loss</span>
                  <span
                    className={`font-mono tabular-nums font-medium ${
                      estimatedGain >= 0 ? "text-green-400" : "text-red-400"
                    }`}
                  >
                    {estimatedGain >= 0 ? "+" : ""}
                    {fmtUSD(estimatedGain)}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-between pt-1">
            <Button
              variant="ghost"
              onClick={() => onOpenChange(false)}
              className="text-zinc-400 hover:text-white hover:bg-zinc-800"
            >
              Cancel
            </Button>
            <Button
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending || !validShares || !validPrice}
              className="bg-red-600 hover:bg-red-500 text-white"
            >
              {mutation.isPending ? "Selling…" : "Confirm Sell"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
