export interface NotificationSettings {
  id: number
  telegram_enabled: boolean
  telegram_chat_id: string | null
  browser_push_enabled: boolean
  whatsapp_enabled: boolean
  whatsapp_phone: string | null
  created_at: string
  updated_at: string | null
}

export interface NotificationSettingsUpdate {
  telegram_enabled?: boolean
  telegram_chat_id?: string | null
  browser_push_enabled?: boolean
  whatsapp_enabled?: boolean
  whatsapp_phone?: string | null
}

export interface TestTelegramRequest {
  chat_id: string
}

export interface TestTelegramResponse {
  success: boolean
  message: string
}

export interface TestWhatsAppRequest {
  phone: string
}

export interface TestWhatsAppResponse {
  success: boolean
  message: string
}
