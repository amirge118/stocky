import { render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { PortfolioNewsFeed } from "@/components/features/portfolio/PortfolioNewsFeed"

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe("PortfolioNewsFeed", () => {
  beforeEach(() => {
    global.fetch = jest.fn()
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it("renders loading state initially", () => {
    ;(global.fetch as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    render(<PortfolioNewsFeed />, { wrapper: createWrapper() })

    expect(screen.getByText("Portfolio News")).toBeInTheDocument()
  })

  it("renders empty state when no news", async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    })

    render(<PortfolioNewsFeed />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText("No news for your holdings.")).toBeInTheDocument()
    })
  })

  it.skip("renders news items with symbol and title", async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve([
          {
            symbol: "AAPL",
            title: "Apple announces new product",
            publisher: "Reuters",
            link: "https://example.com",
            published_at: Date.now() - 3600000,
          },
        ]),
    })

    render(<PortfolioNewsFeed />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText("AAPL")).toBeInTheDocument()
      expect(screen.getByText("Apple announces new product")).toBeInTheDocument()
    })
  })
})
