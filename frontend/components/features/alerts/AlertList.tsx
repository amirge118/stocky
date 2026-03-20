"use client"

import type { Alert } from "@/types/alerts"
import { AlertRow } from "./AlertRow"

interface AlertListProps {
  alerts: Alert[]
  isLoading: boolean
}

export function AlertList({ alerts, isLoading }: AlertListProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-14 rounded-lg bg-zinc-900/50 animate-pulse" />
        ))}
      </div>
    )
  }

  if (alerts.length === 0) {
    return (
      <div className="text-center py-16 text-zinc-500">
        <p className="text-sm">No alerts yet.</p>
        <p className="text-xs mt-1">Create one to get notified when a stock hits your target price.</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {alerts.map((alert) => (
        <AlertRow key={alert.id} alert={alert} />
      ))}
    </div>
  )
}
