import { render, screen } from "@testing-library/react"
import { MarketSnapshotBar } from "@/components/features/market/MarketSnapshotBar"
import type { IndexData, SectorData } from "@/types/market"

const baseIndex = (over: Partial<IndexData> = {}): IndexData => ({
  symbol: "SPY",
  name: "S&P 500",
  price: 100,
  change: 1,
  change_percent: 1,
  sparkline: [],
  ...over,
})

const baseSector = (over: Partial<SectorData> = {}): SectorData => ({
  name: "Tech",
  etf: "XLK",
  price: 100,
  change_percent: 0.5,
  news: [],
  ...over,
})

describe("MarketSnapshotBar", () => {
  it("shows risk-on when most indices are up", () => {
    render(
      <MarketSnapshotBar
        indices={[
          baseIndex({ change_percent: 0.5 }),
          baseIndex({ symbol: "QQQ", change_percent: 0.3 }),
          baseIndex({ symbol: "DIA", change_percent: 0.1 }),
          baseIndex({ symbol: "IWM", change_percent: -0.2 }),
        ]}
        sectors={[]}
      />
    )
    expect(screen.getByText("Risk-on tone")).toBeInTheDocument()
    expect(screen.getByText(/3\/4/)).toBeInTheDocument()
  })

  it("shows sector ETF breadth when sectors provided", () => {
    render(
      <MarketSnapshotBar
        indices={[baseIndex()]}
        sectors={[baseSector({ change_percent: 1 }), baseSector({ name: "Energy", change_percent: -1 })]}
      />
    )
    expect(screen.getByText(/Sector ETFs:/)).toBeInTheDocument()
    expect(screen.getByText(/1\/2/)).toBeInTheDocument()
  })
})
