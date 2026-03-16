import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AddStockDialog } from "@/components/features/stocks/AddStockDialog"

jest.mock("@/lib/api/stocks", () => ({
  createStock: jest.fn(),
  searchStocks: jest.fn().mockResolvedValue([]),
}))

jest.mock("@/hooks/use-toast", () => ({
  useToast: () => ({ toast: jest.fn() }),
}))

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe("AddStockDialog", () => {
  const defaultProps = {
    open: true,
    onOpenChange: jest.fn(),
    onSuccess: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("renders dialog when open", () => {
    render(<AddStockDialog {...defaultProps} />, { wrapper: createWrapper() })
    expect(screen.getByRole("heading", { name: "Add Stock" })).toBeInTheDocument()
    expect(screen.getByLabelText("Symbol")).toBeInTheDocument()
  })

  it("does not render when closed", () => {
    render(<AddStockDialog {...defaultProps} open={false} />, {
      wrapper: createWrapper(),
    })
    expect(screen.queryByText("Add Stock")).not.toBeInTheDocument()
  })

  it("renders search input", () => {
    render(<AddStockDialog {...defaultProps} />, { wrapper: createWrapper() })
    expect(screen.getByLabelText("Symbol")).toBeInTheDocument()
    expect(
      screen.getByPlaceholderText("Search by ticker or company name...")
    ).toBeInTheDocument()
  })

  it("calls onOpenChange when close is clicked", async () => {
    const user = userEvent.setup()
    render(<AddStockDialog {...defaultProps} />, { wrapper: createWrapper() })
    const closeButtons = screen.getAllByRole("button", { name: /close/i })
    await user.click(closeButtons[0])
    expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false)
  })
})
