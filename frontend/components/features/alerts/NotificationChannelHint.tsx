"use client"

import Link from "next/link"
import { useQuery } from "@tanstack/react-query"
import { getNotificationSettings } from "@/lib/api/notificationSettings"

export function NotificationChannelHint() {
  const { data: settings, isPending } = useQuery({
    queryKey: ["notification-settings"],
    queryFn: getNotificationSettings,
    staleTime: 5 * 60 * 1000,
  })

  // Don't render anything while loading or if any channel is configured
  if (isPending || !settings) return null
  if (settings.telegram_chat_id || settings.whatsapp_phone) return null

  return (
    <div className="flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
      <span className="mt-px shrink-0">⚠</span>
      <span>
        No notification channel configured — alerts will only fire in-browser.{" "}
        <Link href="/settings" className="underline underline-offset-2 hover:text-amber-200 transition-colors">
          Go to Settings
        </Link>{" "}
        to add Telegram or WhatsApp.
      </span>
    </div>
  )
}
