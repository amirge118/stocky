import type { IndexData, SectorData } from "@/types/market"

interface MarketSnapshotBarProps {
  indices: IndexData[]
  sectors: SectorData[]
}

/**
 * Compact institutional-style read on index direction and optional sector breadth.
 */
export function MarketSnapshotBar({ indices, sectors }: MarketSnapshotBarProps) {
  const idxUp = indices.filter((i) => i.change_percent >= 0).length
  const idxTotal = indices.length
  const avgIdx =
    idxTotal > 0
      ? indices.reduce((s, i) => s + i.change_percent, 0) / idxTotal
      : 0

  const secTotal = sectors.length
  const secUp = secTotal > 0 ? sectors.filter((s) => s.change_percent >= 0).length : null

  const tone =
    idxTotal === 0
      ? "No benchmark data"
      : idxUp > idxTotal / 2
        ? "Risk-on tone"
        : idxUp < idxTotal / 2
          ? "Risk-off tone"
          : "Mixed benchmarks"

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/80 px-4 py-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
          <span className="font-semibold text-zinc-200 tabular-nums">{tone}</span>
          {idxTotal > 0 && (
            <span className="text-zinc-400">
              Benchmarks:{" "}
              <span className="text-zinc-200 tabular-nums">
                {idxUp}/{idxTotal}
              </span>{" "}
              non-negative
            </span>
          )}
          {idxTotal > 0 && (
            <span className="text-zinc-500">
              Avg day %:{" "}
              <span
                className={`tabular-nums font-medium ${
                  avgIdx >= 0 ? "text-green-400" : "text-red-400"
                }`}
              >
                {avgIdx >= 0 ? "+" : ""}
                {avgIdx.toFixed(2)}%
              </span>
            </span>
          )}
        </div>
        {secTotal > 0 && secUp !== null && (
          <span className="text-xs text-zinc-500 sm:text-right">
            Sector ETFs:{" "}
            <span className="text-zinc-300 tabular-nums">
              {secUp}/{secTotal}
            </span>{" "}
            advancing
          </span>
        )}
      </div>
    </div>
  )
}
