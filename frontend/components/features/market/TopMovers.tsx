import Link from "next/link"
import type { MoverData } from "@/types/market"

interface MoverRowProps {
  mover: MoverData
}

function MoverRow({ mover }: MoverRowProps) {
  const isPositive = mover.change_percent >= 0
  const changeColor = isPositive ? "text-green-400" : "text-red-400"
  const sign = isPositive ? "+" : ""

  return (
    <Link
      href={`/stocks/${mover.symbol}`}
      className="flex items-center justify-between py-2 px-3 rounded-md hover:bg-zinc-800 transition-colors group"
    >
      <div className="flex flex-col min-w-0">
        <span className="text-sm font-semibold text-white group-hover:text-zinc-200">
          {mover.symbol}
        </span>
        <span className="text-xs text-zinc-500 truncate">{mover.name}</span>
      </div>
      <div className="flex flex-col items-end shrink-0">
        <span className="text-sm font-medium text-zinc-200 tabular-nums">
          ${mover.price.toFixed(2)}
        </span>
        <span className={`text-xs font-semibold tabular-nums ${changeColor}`}>
          {sign}{mover.change_percent.toFixed(2)}%
        </span>
      </div>
    </Link>
  )
}

interface TopMoversProps {
  gainers: MoverData[]
  losers: MoverData[]
}

export function TopMovers({ gainers, losers }: TopMoversProps) {
  return (
    <section className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
      <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">
        Top Market Movers
      </h2>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs font-medium text-green-400 mb-2 px-3">Gainers</p>
          <div className="space-y-0.5">
            {gainers.map((m) => (
              <MoverRow key={m.symbol} mover={m} />
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs font-medium text-red-400 mb-2 px-3">Losers</p>
          <div className="space-y-0.5">
            {losers.map((m) => (
              <MoverRow key={m.symbol} mover={m} />
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
