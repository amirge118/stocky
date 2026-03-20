import { fetchAlerts, createAlert, updateAlert, deleteAlert } from "@/lib/api/alerts"
import * as client from "@/lib/api/client"

jest.mock("@/lib/api/client")

const mockAlert = {
  id: 1,
  ticker: "AAPL",
  condition_type: "ABOVE" as const,
  target_price: "200.0000",
  is_active: true,
  last_triggered: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: null,
}

describe("Alert API functions", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe("fetchAlerts", () => {
    it("calls get with default limit and offset", async () => {
      ;(client.get as jest.Mock).mockResolvedValue([mockAlert])
      const result = await fetchAlerts()
      expect(client.get).toHaveBeenCalledWith("/api/v1/alerts?limit=50&offset=0")
      expect(result).toEqual([mockAlert])
    })

    it("calls get with custom limit and offset", async () => {
      ;(client.get as jest.Mock).mockResolvedValue([])
      await fetchAlerts(10, 20)
      expect(client.get).toHaveBeenCalledWith("/api/v1/alerts?limit=10&offset=20")
    })
  })

  describe("createAlert", () => {
    it("calls post with correct endpoint and payload", async () => {
      ;(client.post as jest.Mock).mockResolvedValue(mockAlert)
      const payload = { ticker: "AAPL", condition_type: "ABOVE" as const, target_price: 200 }
      const result = await createAlert(payload)
      expect(client.post).toHaveBeenCalledWith("/api/v1/alerts", payload)
      expect(result).toEqual(mockAlert)
    })
  })

  describe("updateAlert", () => {
    it("calls patch with correct endpoint and payload", async () => {
      const updated = { ...mockAlert, is_active: false }
      ;(client.patch as jest.Mock).mockResolvedValue(updated)
      const result = await updateAlert(1, { is_active: false })
      expect(client.patch).toHaveBeenCalledWith("/api/v1/alerts/1", { is_active: false })
      expect(result).toEqual(updated)
    })

    it("calls patch with target_price update", async () => {
      ;(client.patch as jest.Mock).mockResolvedValue(mockAlert)
      await updateAlert(42, { target_price: 300 })
      expect(client.patch).toHaveBeenCalledWith("/api/v1/alerts/42", { target_price: 300 })
    })
  })

  describe("deleteAlert", () => {
    it("calls del with correct endpoint", async () => {
      ;(client.del as jest.Mock).mockResolvedValue(undefined)
      await deleteAlert(1)
      expect(client.del).toHaveBeenCalledWith("/api/v1/alerts/1")
    })
  })
})
