export type ConditionType = "ABOVE" | "BELOW" | "EQUAL"

export interface Alert {
  id: number
  ticker: string
  condition_type: ConditionType
  target_price: string
  is_active: boolean
  last_triggered: string | null
  created_at: string
  updated_at: string | null
}

export interface AlertCreate {
  ticker: string
  condition_type: ConditionType
  target_price: number
}

export interface AlertUpdate {
  is_active?: boolean
  target_price?: number
}
