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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Bell } from "lucide-react"
import { useAlerts } from "@/lib/hooks/useAlerts"

export interface AlertDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  symbol?: string
}

export function AlertDialog({ open, onOpenChange, symbol: initialSymbol }: AlertDialogProps) {
  const { addAlert } = useAlerts()
  const [symbol, setSymbol] = useState(initialSymbol?.toUpperCase() ?? "")
  const [targetPrice, setTargetPrice] = useState("")
  const [direction, setDirection] = useState<"above" | "below">("above")

  const handleSubmit = () => {
    const price = parseFloat(targetPrice)
    if (!symbol.trim() || isNaN(price) || price <= 0) return

    addAlert(symbol.trim().toUpperCase(), price, direction)
    setTargetPrice("")
    if (!initialSymbol) setSymbol("")
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px] bg-zinc-900 border-zinc-700">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Bell size={18} />
            Price Alert
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-zinc-300">Symbol</Label>
            <Input
              placeholder="e.g. AAPL"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="bg-zinc-800 border-zinc-600 text-white font-mono"
              disabled={!!initialSymbol}
            />
          </div>

          <div className="space-y-1.5">
            <Label className="text-zinc-300">Notify when price goes</Label>
            <Select value={direction} onValueChange={(v) => setDirection(v as "above" | "below")}>
              <SelectTrigger className="bg-zinc-800 border-zinc-600 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="above">Above</SelectItem>
                <SelectItem value="below">Below</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label className="text-zinc-300">Target price ($)</Label>
            <Input
              type="number"
              min="0.01"
              step="any"
              placeholder="e.g. 150.00"
              value={targetPrice}
              onChange={(e) => setTargetPrice(e.target.value)}
              className="bg-zinc-800 border-zinc-600 text-white"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="border-zinc-600 text-zinc-300"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!symbol.trim() || !targetPrice || parseFloat(targetPrice) <= 0}
              className="bg-blue-600 hover:bg-blue-500 text-white"
            >
              Add Alert
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
