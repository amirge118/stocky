import { render, screen, fireEvent } from "@testing-library/react"
import { BulkActionsBar } from "@/components/features/stocks/BulkActionsBar"
import type { Stock } from "@/types/stock"

// Mock useWatchlist hook
jest.mock("@/lib/hooks/useWatchlist", () => ({
  useWatchlist: jest.fn(() => ({
    isInWatchlist: jest.fn((symbol: string) => symbol === "AAPL"),
    toggleWatchlist: jest.fn(),
  })),
}))

const mockStocks: Stock[] = [
  {
    id: 1,
    symbol: "AAPL",
    name: "Apple Inc.",
    exchange: "NASDAQ",
    sector: "Technology",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: null,
  },
  {
    id: 2,
    symbol: "MSFT",
    name: "Microsoft Corporation",
    exchange: "NASDAQ",
    sector: "Technology",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: null,
  },
]

describe("BulkActionsBar", () => {
  const defaultProps = {
    selectedStocks: [mockStocks[0]],
    allStocks: mockStocks,
    onSelectAll: jest.fn(),
    onDeselectAll: jest.fn(),
    onBulkDelete: jest.fn(),
    onBulkAddToWatchlist: jest.fn(),
    onBulkRemoveFromWatchlist: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("does not render when no stocks are selected", () => {
    const { container } = render(
      <BulkActionsBar {...defaultProps} selectedStocks={[]} />
    )

    expect(container.firstChild).toBeNull()
  })

  it("renders selected count", () => {
    render(<BulkActionsBar {...defaultProps} />)

    expect(screen.getByText("1 stock selected")).toBeInTheDocument()
  })

  it("renders plural form for multiple stocks", () => {
    render(
      <BulkActionsBar {...defaultProps} selectedStocks={mockStocks} />
    )

    expect(screen.getByText("2 stocks selected")).toBeInTheDocument()
  })

  it("calls onSelectAll when select all checkbox is checked", () => {
    render(<BulkActionsBar {...defaultProps} />)

    const checkboxes = screen.getAllByRole("checkbox")
    const selectAllCheckbox = checkboxes[0]
    fireEvent.click(selectAllCheckbox)

    expect(defaultProps.onSelectAll).toHaveBeenCalled()
  })

  it("calls onDeselectAll when select all checkbox is unchecked", () => {
    render(
      <BulkActionsBar
        {...defaultProps}
        selectedStocks={mockStocks}
        allStocks={mockStocks}
      />
    )

    const checkboxes = screen.getAllByRole("checkbox")
    const selectAllCheckbox = checkboxes[0]
    fireEvent.click(selectAllCheckbox)

    expect(defaultProps.onDeselectAll).toHaveBeenCalled()
  })

  it("calls onBulkDelete when delete button is clicked", () => {
    render(<BulkActionsBar {...defaultProps} />)

    const deleteButton = screen.getByText("Delete Selected")
    fireEvent.click(deleteButton)

    expect(defaultProps.onBulkDelete).toHaveBeenCalledWith([mockStocks[0]])
  })

  it("shows add to watchlist when stocks are not in watchlist", () => {
    const { useWatchlist } = require("@/lib/hooks/useWatchlist")
    useWatchlist.mockReturnValue({
      isInWatchlist: jest.fn(() => false),
      toggleWatchlist: jest.fn(),
    })

    render(<BulkActionsBar {...defaultProps} />)

    expect(screen.getByText("Add to Watchlist")).toBeInTheDocument()
  })

  it("shows remove from watchlist when stocks are in watchlist", () => {
    const { useWatchlist } = require("@/lib/hooks/useWatchlist")
    useWatchlist.mockReturnValue({
      isInWatchlist: jest.fn(() => true),
      toggleWatchlist: jest.fn(),
    })

    render(<BulkActionsBar {...defaultProps} />)

    expect(screen.getByText("Remove from Watchlist")).toBeInTheDocument()
  })

  it("calls onBulkAddToWatchlist when adding to watchlist", () => {
    const { useWatchlist } = require("@/lib/hooks/useWatchlist")
    useWatchlist.mockReturnValue({
      isInWatchlist: jest.fn(() => false),
      toggleWatchlist: jest.fn(),
    })

    render(<BulkActionsBar {...defaultProps} />)

    const addButton = screen.getByText("Add to Watchlist")
    fireEvent.click(addButton)

    expect(defaultProps.onBulkAddToWatchlist).toHaveBeenCalledWith([
      mockStocks[0],
    ])
  })

  it("shows selected symbols badge when 5 or fewer stocks selected", () => {
    render(<BulkActionsBar {...defaultProps} />)

    expect(screen.getByText("AAPL")).toBeInTheDocument()
  })

  it("does not show symbols badge when more than 5 stocks selected", () => {
    const manyStocks = Array.from({ length: 6 }, (_, i) => ({
      ...mockStocks[0],
      id: i + 1,
      symbol: `STOCK${i + 1}`,
    }))

    render(
      <BulkActionsBar {...defaultProps} selectedStocks={manyStocks} />
    )

    expect(screen.queryByText("STOCK1")).not.toBeInTheDocument()
  })
})
