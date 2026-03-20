"use client"

import { useState, useEffect } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useToast } from "@/hooks/use-toast"
import {
  getNotificationSettings,
  updateNotificationSettings,
  testTelegramConnection,
  testWhatsAppConnection,
} from "@/lib/api/notificationSettings"

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  const { data: settings, isPending, isError, refetch } = useQuery({
    queryKey: ["notification-settings"],
    queryFn: getNotificationSettings,
  })

  const [chatIdDraft, setChatIdDraft] = useState("")
  const [whatsappDraft, setWhatsappDraft] = useState("")

  useEffect(() => {
    if (settings) {
      setChatIdDraft(settings.telegram_chat_id ?? "")
      setWhatsappDraft(settings.whatsapp_phone ?? "")
    }
  }, [settings])

  const updateMutation = useMutation({
    mutationFn: updateNotificationSettings,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notification-settings"] }),
    onError: () => toast({ variant: "destructive", title: "Failed to update settings" }),
  })

  const saveChatIdMutation = useMutation({
    mutationFn: updateNotificationSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notification-settings"] })
      toast({ title: "Telegram Chat ID saved" })
    },
    onError: () => toast({ variant: "destructive", title: "Failed to save Chat ID" }),
  })

  const saveWhatsappMutation = useMutation({
    mutationFn: updateNotificationSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notification-settings"] })
      toast({ title: "WhatsApp number saved" })
    },
    onError: () => toast({ variant: "destructive", title: "Failed to save WhatsApp number" }),
  })

  const testTelegramMutation = useMutation({
    mutationFn: testTelegramConnection,
    onSuccess: (data) =>
      toast({ variant: data.success ? "default" : "destructive", title: data.message }),
    onError: () => toast({ variant: "destructive", title: "Failed to send Telegram test" }),
  })

  const testWhatsappMutation = useMutation({
    mutationFn: testWhatsAppConnection,
    onSuccess: (data) =>
      toast({ variant: data.success ? "default" : "destructive", title: data.message }),
    onError: () => toast({ variant: "destructive", title: "Failed to send WhatsApp test" }),
  })

  if (isError) {
    return (
      <div className="bg-zinc-950 min-h-screen">
        <div className="max-w-5xl mx-auto px-4 py-8">
          <div className="rounded-xl border border-red-800 bg-red-900/20 p-6 text-red-400 flex items-center justify-between">
            <span>Failed to load notification settings.</span>
            <Button variant="outline" size="sm" onClick={() => refetch()}>Retry</Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-zinc-950 min-h-screen">
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        <div>
          <h1 className="text-xl font-semibold text-white">Settings</h1>
          <p className="text-sm text-zinc-400 mt-1">Manage notification channels and integrations.</p>
        </div>

        {/* Notification Channels — toggles */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 space-y-6">
          <h2 className="text-sm font-semibold text-white uppercase tracking-wide">Notification Channels</h2>

          {isPending ? (
            <div className="space-y-4 animate-pulse">
              <div className="h-12 bg-zinc-800 rounded-lg" />
              <div className="h-12 bg-zinc-800 rounded-lg" />
              <div className="h-12 bg-zinc-800 rounded-lg" />
            </div>
          ) : (
            <>
              {/* Browser Push */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-white">Browser Push</p>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    Show desktop notifications when an alert triggers (requires browser permission).
                  </p>
                </div>
                <Switch
                  checked={settings!.browser_push_enabled}
                  onCheckedChange={(checked) => updateMutation.mutate({ browser_push_enabled: checked })}
                />
              </div>

              <div className="border-t border-zinc-800" />

              {/* Telegram */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-white">Telegram</p>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    Send alert messages to your Telegram chat.
                    {!settings!.telegram_chat_id && (
                      <span className="ml-1 text-amber-400">Save a Chat ID first to enable.</span>
                    )}
                  </p>
                </div>
                <Switch
                  checked={settings!.telegram_enabled}
                  disabled={!settings!.telegram_chat_id}
                  onCheckedChange={(checked) => updateMutation.mutate({ telegram_enabled: checked })}
                />
              </div>

              <div className="border-t border-zinc-800" />

              {/* WhatsApp */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-white">WhatsApp</p>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    Send alert messages to your WhatsApp number.
                    {!settings!.whatsapp_phone && (
                      <span className="ml-1 text-amber-400">Save a phone number first to enable.</span>
                    )}
                  </p>
                </div>
                <Switch
                  checked={settings!.whatsapp_enabled}
                  disabled={!settings!.whatsapp_phone}
                  onCheckedChange={(checked) => updateMutation.mutate({ whatsapp_enabled: checked })}
                />
              </div>
            </>
          )}
        </div>

        {/* Telegram Configuration */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 space-y-4">
          <h2 className="text-sm font-semibold text-white uppercase tracking-wide">Telegram Configuration</h2>
          <p className="text-sm text-zinc-400">
            To find your Chat ID: open Telegram, message{" "}
            <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-200 text-xs">@userinfobot</code>{" "}
            and send{" "}
            <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-200 text-xs">/start</code>.
            It will reply with your numeric ID.
          </p>
          {isPending ? (
            <div className="animate-pulse h-10 bg-zinc-800 rounded-lg" />
          ) : (
            <div className="flex gap-2">
              <Input
                placeholder="e.g. 123456789"
                value={chatIdDraft}
                onChange={(e) => setChatIdDraft(e.target.value)}
                className="bg-zinc-800 border-zinc-700 text-white placeholder-zinc-500 font-mono"
              />
              <Button
                variant="outline"
                onClick={() => saveChatIdMutation.mutate({ telegram_chat_id: chatIdDraft.trim() || null })}
                disabled={saveChatIdMutation.isPending}
              >
                {saveChatIdMutation.isPending ? "Saving…" : "Save"}
              </Button>
              <Button
                variant="outline"
                onClick={() =>
                  testTelegramMutation.mutate({
                    chat_id: chatIdDraft || settings!.telegram_chat_id || "",
                  })
                }
                disabled={!(chatIdDraft || settings!.telegram_chat_id) || testTelegramMutation.isPending}
              >
                {testTelegramMutation.isPending ? "Sending…" : "Test Connection"}
              </Button>
            </div>
          )}
        </div>

        {/* WhatsApp Configuration */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 space-y-4">
          <h2 className="text-sm font-semibold text-white uppercase tracking-wide">WhatsApp Configuration</h2>
          <p className="text-sm text-zinc-400">
            Uses the{" "}
            <span className="text-zinc-200">Meta WhatsApp Business Cloud API</span>.
            Enter your phone number in international format (e.g.{" "}
            <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-200 text-xs">+12025550123</code>).
            The server must have <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-200 text-xs">WHATSAPP_TOKEN</code> and{" "}
            <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-200 text-xs">WHATSAPP_PHONE_NUMBER_ID</code> set.
          </p>
          {isPending ? (
            <div className="animate-pulse h-10 bg-zinc-800 rounded-lg" />
          ) : (
            <div className="flex gap-2">
              <Input
                placeholder="e.g. +12025550123"
                value={whatsappDraft}
                onChange={(e) => setWhatsappDraft(e.target.value)}
                className="bg-zinc-800 border-zinc-700 text-white placeholder-zinc-500 font-mono"
              />
              <Button
                variant="outline"
                onClick={() => saveWhatsappMutation.mutate({ whatsapp_phone: whatsappDraft.trim() || null })}
                disabled={saveWhatsappMutation.isPending}
              >
                {saveWhatsappMutation.isPending ? "Saving…" : "Save"}
              </Button>
              <Button
                variant="outline"
                onClick={() =>
                  testWhatsappMutation.mutate({
                    phone: whatsappDraft || settings!.whatsapp_phone || "",
                  })
                }
                disabled={!(whatsappDraft || settings!.whatsapp_phone) || testWhatsappMutation.isPending}
              >
                {testWhatsappMutation.isPending ? "Sending…" : "Test Connection"}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
