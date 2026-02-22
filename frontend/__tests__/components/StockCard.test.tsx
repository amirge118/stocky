import { render, screen } from "@testing-library/react"
import { StockCard } from "@/components/features/stocks/StockCard"
import { Stock } from "@/types/stock"

const mockStock: Stock = {
  id: 1,
  symbol: "AAPL",
  name: "Apple Inc.",
  exchange: "NASDAQ",
  sector: "Technology",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
}

describe("StockCard", () => {
  it("renders stock information correctly", () => {
    render(<StockCard stock={mockStock} />)

    expect(screen.getByText("AAPL")).toBeInTheDocument()
    expect(screen.getByText("Apple Inc.")).toBeInTheDocument()
    expect(screen.getByText("NASDAQ")).toBeInTheDocument()
    expect(screen.getByText("Technology")).toBeInTheDocument()
  })

  it("renders without sector when not provided", () => {
    const stockWithoutSector = { ...mockStock, sector: null }
    render(<StockCard stock={stockWithoutSector} />)

    expect(screen.getByText("AAPL")).toBeInTheDocument()
    expect(screen.queryByText("Sector:")).not.toBeInTheDocument()
  })

  it("calls onSelect when card is clicked", () => {
    const onSelect = jest.fn()
    render(<StockCard stock={mockStock} onSelect={onSelect} />)

    const card = screen.getByText("AAPL").closest("div")
    card?.click()

    expect(onSelect).toHaveBeenCalledWith("AAPL")
    expect(onSelect).toHaveBeenCalledTimes(1)
  })

  it("does not call onSelect when not provided", () => {
    render(<StockCard stock={mockStock} />)

    const card = screen.getByText("AAPL").closest("div")
    card?.click()

    // Should not throw error
    expect(card).toBeInTheDocument()
  })

  it("applies cursor-pointer class when onSelect is provided", () => {
    const onSelect = jest.fn()
    const { container } = render(<StockCard stock={mockStock} onSelect={onSelect} />)

    const card = container.querySelector(".cursor-pointer")
    expect(card).toBeInTheDocument()
  })

  it("does not apply cursor-pointer class when onSelect is not provided", () => {
    const { container } = render(<StockCard stock={mockStock} />)

    const card = container.querySelector(".cursor-pointer")
    expect(card).not.toBeInTheDocument()
  })
})
