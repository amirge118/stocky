import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AddStockDialog } from "@/components/features/stocks/AddStockDialog"

// Mock the API
jest.mock("@/lib/api/stocks", () => ({
  createStock: jest.fn(),
}))

// Mock toast
jest.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
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
    expect(
      screen.getByText("Add a new stock to your portfolio. Enter the stock details below.")
    ).toBeInTheDocument()
  })

  it("does not render when closed", () => {
    render(<AddStockDialog {...defaultProps} open={false} />, {
      wrapper: createWrapper(),
    })

    expect(screen.queryByText("Add Stock")).not.toBeInTheDocument()
  })

  it("renders all form fields", () => {
    render(<AddStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    expect(screen.getByLabelText(/symbol/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/exchange/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/sector/i)).toBeInTheDocument()
  })

  it("shows validation errors for empty required fields", async () => {
    const user = userEvent.setup()
    render(<AddStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    const submitButton = screen.getByRole("button", { name: "Add Stock" })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText("Symbol is required")).toBeInTheDocument()
    })
  })

  it("validates symbol length", async () => {
    const user = userEvent.setup()
    render(<AddStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    const symbolInput = screen.getByLabelText(/symbol/i)
    await user.type(symbolInput, "A".repeat(11))

    const submitButton = screen.getByRole("button", { name: "Add Stock" })
    await user.click(submitButton)

    await waitFor(() => {
      expect(
        screen.getByText("Symbol must be 10 characters or less")
      ).toBeInTheDocument()
    })
  })

  it("validates name length", async () => {
    const user = userEvent.setup()
    render(<AddStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    const nameInput = screen.getByLabelText(/name/i)
    await user.type(nameInput, "A".repeat(256))

    const submitButton = screen.getByRole("button", { name: "Add Stock" })
    await user.click(submitButton)

    await waitFor(() => {
      expect(
        screen.getByText("Name must be 255 characters or less")
      ).toBeInTheDocument()
    })
  })

  it("converts symbol to uppercase", async () => {
    const user = userEvent.setup()
    const { createStock } = require("@/lib/api/stocks")
    createStock.mockResolvedValue({
      id: 1,
      symbol: "AAPL",
      name: "Apple Inc.",
      exchange: "NASDAQ",
    })

    render(<AddStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    const symbolInput = screen.getByLabelText(/symbol/i)
    await user.type(symbolInput, "aapl")

    const nameInput = screen.getByLabelText(/name/i)
    await user.type(nameInput, "Apple Inc.")

    const submitButton = screen.getByRole("button", { name: "Add Stock" })
    await user.click(submitButton)

    await waitFor(() => {
      expect(createStock).toHaveBeenCalledWith(
        expect.objectContaining({
          symbol: "AAPL",
        })
      )
    })
  })

  it("calls onOpenChange when cancel is clicked", async () => {
    const user = userEvent.setup()
    render(<AddStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    const cancelButton = screen.getByText("Cancel")
    await user.click(cancelButton)

    expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false)
  })

  it("resets form when dialog is closed", async () => {
    const user = userEvent.setup()
    render(<AddStockDialog {...defaultProps} />, { wrapper: createWrapper() })

    const symbolInput = screen.getByLabelText(/symbol/i)
    await user.type(symbolInput, "AAPL")

    const cancelButton = screen.getByText("Cancel")
    await user.click(cancelButton)

    // Reopen dialog
    render(<AddStockDialog {...defaultProps} open={true} />, {
      wrapper: createWrapper(),
    })

    const symbolInputAfter = screen.getByLabelText(/symbol/i)
    expect(symbolInputAfter).toHaveValue("")
  })
})
