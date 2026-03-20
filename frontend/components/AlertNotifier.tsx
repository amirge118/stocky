"use client"

import { useAlertChecker } from "@/lib/hooks/useAlertChecker"

export default function AlertNotifier() {
  useAlertChecker()
  return null
}
