import type {
  NotificationSettings,
  NotificationSettingsUpdate,
  TestTelegramRequest,
  TestTelegramResponse,
  TestWhatsAppRequest,
  TestWhatsAppResponse,
} from "@/types/notificationSettings"
import { get, patch, post } from "./client"

export function getNotificationSettings(): Promise<NotificationSettings> {
  return get<NotificationSettings>("/api/v1/settings/notifications")
}

export function updateNotificationSettings(
  data: NotificationSettingsUpdate
): Promise<NotificationSettings> {
  return patch<NotificationSettings>("/api/v1/settings/notifications", data)
}

export function testTelegramConnection(
  data: TestTelegramRequest
): Promise<TestTelegramResponse> {
  return post<TestTelegramResponse>("/api/v1/settings/notifications/test/telegram", data)
}

export function testWhatsAppConnection(
  data: TestWhatsAppRequest
): Promise<TestWhatsAppResponse> {
  return post<TestWhatsAppResponse>("/api/v1/settings/notifications/test/whatsapp", data)
}
