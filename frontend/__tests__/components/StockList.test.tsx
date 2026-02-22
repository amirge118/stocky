import { render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { StockList } from "@/components/features/stocks/StockList"
import * as stocksApi from "@/lib/api/stocks"

// Mock the API
jest.mock("@/lib/api/stocks")

const mockStocks = {
  data: [
    {
      id: 1,
      symbol: "AAPL",
      name: "Apple Inc.",
      exchange: "NASDAQ",
      sector: "Technology",
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    },
    {
      id: 2,
      symbol: "GOOGL",
      name: "Alphabet Inc.",
      exchange: "NASDAQ",
      sector: "Technology",
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    },
  ],
  meta: {
    page: 1,
    limit: 20,
    total: 2,
    total_pages: 1,
  },
}

describe("StockList", () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    })
    jest.clearAllMocks()
  })

  it("renders loading state", () => {
    ;(stocksApi.getStocks as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    render(
      <QueryClientProvider client={queryClient}>
        <StockList />
      </QueryClientProvider>
    )

    expect(screen.getByRole("status")).toBeInTheDocument()
  })

  it("renders stocks when data is loaded", async () => {
    ;(stocksApi.getStocks as jest.Mock).mockResolvedValue(mockStocks)

    render(
      <QueryClientProvider client={queryClient}>
        <StockList />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText("AAPL")).toBeInTheDocument()
      expect(screen.getByText("GOOGL")).toBeInTheDocument()
    })
  })

  it("renders empty state when no stocks", async () => {
    ;(stocksApi.getStocks as jest.Mock).mockResolvedValue({
      data: [],
      meta: {
        page: 1,
        limit: 20,
        total: 0,
        total_pages: 0,
      },
    })

    render(
      <QueryClientProvider client={queryClient}>
        <StockList />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText("No stocks found.")).toBeInTheDocument()
    })
  })

  it("calls onStockClick when stock is clicked", async () => {
    const onStockClick = jest.fn()
    ;(stocksApi.getStocks as jest.Mock).mockResolvedValue(mockStocks)

    render(
      <QueryClientProvider client={queryClient}>
        <StockList onStockClick={onStockClick} />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText("AAPL")).toBeInTheDocument()
    })

    const card = screen.getByText("AAPL").closest("div")
    card?.click()

    expect(onStockClick).toHaveBeenCalledWith("AAPL")
  })

  it("uses custom page and limit props", async () => {
    ;(stocksApi.getStocks as jest.Mock).mockResolvedValue(mockStocks)

    render(
      <QueryClientProvider client={queryClient}>
        <StockList page={2} limit={10} />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(stocksApi.getStocks).toHaveBeenCalledWith({ page: 2, limit: 10 })
    })
  })
})
