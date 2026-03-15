import { render, screen } from "@testing-library/react"
import { PortfolioSummaryCard } from "@/components/features/portfolio/PortfolioSummaryCard"
import type { PortfolioSummary } from "@/types/portfolio"

const mockSummary: PortfolioSummary = {
  positions: [
    {
      symbol: "AAPL",
      name: "Apple Inc.",
      shares: 10,
      avg_cost: 150,
      total_cost: 1500,
      current_price: 155,
      current_value: 1550,
      gain_loss: 50,
      gain_loss_pct: 3.33,
      portfolio_pct: 50,
      day_change: 50,
      day_change_percent: 3.33,
    },
    {
      symbol: "MSFT",
      name: "Microsoft",
      shares: 5,
      avg_cost: 300,
      total_cost: 1500,
      current_price: 290,
      current_value: 1450,
      gain_loss: -50,
      gain_loss_pct: -3.33,
      portfolio_pct: 50,
      day_change: -25,
      day_change_percent: -1.67,
    },
  ],
  total_value: 3000,
  total_cost: 3000,
  total_gain_loss: 0,
  total_gain_loss_pct: 0,
  total_day_change: 25,
  total_day_change_pct: 0.83,
}

describe("PortfolioSummaryCard", () => {
  it("renders loading skeleton when isPending", () => {
    render(<PortfolioSummaryCard summary={undefined} isPending={true} />)

    const skeleton = document.querySelector(".animate-pulse")
    expect(skeleton).toBeInTheDocument()
  })

  it("returns null when no summary and not pending", () => {
    const { container } = render(
      <PortfolioSummaryCard summary={undefined} isPending={false} />
    )

    expect(container.firstChild).toBeNull()
  })

  it("renders total value and cost basis", () => {
    render(<PortfolioSummaryCard summary={mockSummary} isPending={false} />)

    expect(screen.getByText("Total Value")).toBeInTheDocument()
    expect(screen.getByText("Cost Basis")).toBeInTheDocument()
    expect(screen.getAllByText(/\$3\.0K/).length).toBeGreaterThan(0)
  })

  it("renders Day P&L when total_day_change is present", () => {
    render(<PortfolioSummaryCard summary={mockSummary} isPending={false} />)

    expect(screen.getByText("Today")).toBeInTheDocument()
    expect(screen.getAllByText(/\+?\$25/).length).toBeGreaterThan(0)
    expect(screen.getByText("+0.83%")).toBeInTheDocument()
  })

  it.skip("renders Today's Movers with leaders and losers", () => {
    render(<PortfolioSummaryCard summary={mockSummary} isPending={false} />)

    expect(screen.getByText("Today's movers")).toBeInTheDocument()
    expect(screen.getByText("Leaders:")).toBeInTheDocument()
    expect(screen.getByText("Losers:")).toBeInTheDocument()
    expect(screen.getByText("AAPL")).toBeInTheDocument()
    expect(screen.getByText("MSFT")).toBeInTheDocument()
  })

  it("does not render Day P&L when total_day_change is null", () => {
    const summaryWithoutDay = {
      ...mockSummary,
      total_day_change: null,
      total_day_change_pct: null,
      positions: mockSummary.positions.map((p) => ({
        ...p,
        day_change: null,
        day_change_percent: null,
      })),
    }
    render(<PortfolioSummaryCard summary={summaryWithoutDay} isPending={false} />)

    expect(screen.queryByText("Today")).not.toBeInTheDocument()
    expect(screen.queryByText("Today's movers")).not.toBeInTheDocument()
  })
})
