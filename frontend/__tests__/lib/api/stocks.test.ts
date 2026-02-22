import { getStocks, getStock, createStock, updateStock, deleteStock, fetchStockData } from "@/lib/api/stocks"
import * as client from "@/lib/api/client"

jest.mock("@/lib/api/client")

describe("Stock API functions", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe("getStocks", () => {
    it("calls get with correct endpoint and query params", async () => {
      const mockResponse = {
        data: [],
        meta: { page: 1, limit: 20, total: 0, total_pages: 0 },
      }
      ;(client.get as jest.Mock).mockResolvedValue(mockResponse)

      await getStocks({ page: 2, limit: 10 })

      expect(client.get).toHaveBeenCalledWith("/api/v1/stocks?page=2&limit=10")
    })

    it("calls get without query params when options not provided", async () => {
      const mockResponse = {
        data: [],
        meta: { page: 1, limit: 20, total: 0, total_pages: 0 },
      }
      ;(client.get as jest.Mock).mockResolvedValue(mockResponse)

      await getStocks()

      expect(client.get).toHaveBeenCalledWith("/api/v1/stocks")
    })
  })

  describe("getStock", () => {
    it("calls get with correct endpoint", async () => {
      const mockStock = {
        id: 1,
        symbol: "AAPL",
        name: "Apple Inc.",
        exchange: "NASDAQ",
        sector: "Technology",
      }
      ;(client.get as jest.Mock).mockResolvedValue(mockStock)

      const result = await getStock("AAPL")

      expect(client.get).toHaveBeenCalledWith("/api/v1/stocks/AAPL")
      expect(result).toEqual(mockStock)
    })
  })

  describe("createStock", () => {
    it("calls post with correct endpoint and data", async () => {
      const stockData = {
        symbol: "AAPL",
        name: "Apple Inc.",
        exchange: "NASDAQ",
        sector: "Technology",
      }
      const mockStock = { id: 1, ...stockData }
      ;(client.post as jest.Mock).mockResolvedValue(mockStock)

      const result = await createStock(stockData)

      expect(client.post).toHaveBeenCalledWith("/api/v1/stocks", stockData)
      expect(result).toEqual(mockStock)
    })
  })

  describe("updateStock", () => {
    it("calls put with correct endpoint and data", async () => {
      const updateData = { name: "Apple Corporation" }
      const mockStock = {
        id: 1,
        symbol: "AAPL",
        name: "Apple Corporation",
        exchange: "NASDAQ",
      }
      ;(client.put as jest.Mock).mockResolvedValue(mockStock)

      const result = await updateStock("AAPL", updateData)

      expect(client.put).toHaveBeenCalledWith("/api/v1/stocks/AAPL", updateData)
      expect(result).toEqual(mockStock)
    })
  })

  describe("deleteStock", () => {
    it("calls del with correct endpoint", async () => {
      ;(client.del as jest.Mock).mockResolvedValue(undefined)

      await deleteStock("AAPL")

      expect(client.del).toHaveBeenCalledWith("/api/v1/stocks/AAPL")
    })
  })

  describe("fetchStockData", () => {
    it("calls get with correct endpoint", async () => {
      const mockData = {
        symbol: "AAPL",
        current_price: 150.0,
        change: 5.0,
        change_percent: 3.33,
      }
      ;(client.get as jest.Mock).mockResolvedValue(mockData)

      const result = await fetchStockData("AAPL")

      expect(client.get).toHaveBeenCalledWith("/api/v1/stocks/AAPL/data")
      expect(result).toEqual(mockData)
    })
  })
})
