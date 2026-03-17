"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { fetchAlerts } from "@/lib/api/alerts"
import { AlertList } from "@/components/features/alerts/AlertList"
import { AlertCreateDialog } from "@/components/features/alerts/AlertCreateDialog"
import { Button } from "@/components/ui/button"
import type { Alert } from "@/types/alerts"

export default function AlertsPage() {
  const [dialogOpen, setDialogOpen] = useState(false)

  const { data: alerts = [], isLoading } = useQuery<Alert[]>({
    queryKey: ["alerts"],
    queryFn: () => fetchAlerts(),
    refetchInterval: 60_000,
  })

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-white">Price Alerts</h1>
          <p className="text-sm text-zinc-500 mt-0.5">
            Get notified via Telegram when a stock hits your target price.
          </p>
        </div>
        <Button
          onClick={() => setDialogOpen(true)}
          className="bg-zinc-100 text-zinc-900 hover:bg-white text-sm"
        >
          + New Alert
        </Button>
      </div>

      <AlertList alerts={alerts} isLoading={isLoading} />

      <AlertCreateDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  )
}
