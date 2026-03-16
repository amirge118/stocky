"use client"

import { useQueries } from "@tanstack/react-query"
import Link from "next/link"
import { getStockInfo, fetchStockData } from "@/lib/api/stocks"
import type { StockInfoResponse } from "@/types/stock"

interface CompareFundamentalsTableProps {
  symbols: string[]
}

function fmtUSD(n: number | null): string {
  if (n === null) return "—"
  if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`
  return n?.toLocaleString("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 }) ?? "—"
}

function fmtPct(n: number | null): string {
  if (n === null) return "—"
  return `${(n * 100).toFixed(2)}%`
}

export function CompareFundamentalsTable({ symbols }: CompareFundamentalsTableProps) {
  const infoQueries = useQueries({
    queries: symbols.map((symbol) => ({
      queryKey: ["stock-info", symbol],
      queryFn: () => getStockInfo(symbol),
      staleTime: 10 * 60_000,
    })),
  })

  const dataQueries = useQueries({
    queries: symbols.map((symbol) => ({
      queryKey: ["stock-data", symbol],
      queryFn: () => fetchStockData(symbol),
      staleTime: 60_000,
    })),
  })

  const isLoading = infoQueries.some((q) => q.isPending) || dataQueries.some((q) => q.isPending)
  const infos = infoQueries.map((q) => q.data)
  const datas = dataQueries.map((q) => q.data)

  if (isLoading) {
    return (
      <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6 animate-pulse">
        <div className="h-48 rounded bg-zinc-800" />
      </div>
    )
  }

  type StockData = { current_price?: number; change_percent?: number }
  const metrics: { label: string; get: (info: StockInfoResponse | undefined, data: StockData | undefined) => string }[] = [
    { label: "Price", get: (_, d) => fmtUSD(d?.current_price ?? null) },
    { label: "Day %", get: (_, d) => (d?.change_percent != null ? `${d.change_percent >= 0 ? "+" : ""}${d.change_percent.toFixed(2)}%` : "—") },
    { label: "Market Cap", get: (i) => fmtUSD(i?.market_cap ?? null) },
    { label: "P/E", get: (i) => (i?.pe_ratio != null ? `${i.pe_ratio.toFixed(1)}x` : "—") },
    { label: "Forward P/E", get: (i) => (i?.forward_pe != null ? `${i.forward_pe.toFixed(1)}x` : "—") },
    { label: "Dividend Yield", get: (i) => fmtPct(i?.dividend_yield ?? null) },
    { label: "Beta", get: (i) => (i?.beta != null ? i.beta.toFixed(2) : "—") },
    { label: "52W High", get: (i) => fmtUSD(i?.fifty_two_week_high ?? null) },
    { label: "52W Low", get: (i) => fmtUSD(i?.fifty_two_week_low ?? null) },
  ]

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 overflow-hidden">
      <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wide px-5 py-3 border-b border-zinc-800">
        Fundamentals
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800/60">
              <th className="text-left px-5 py-2.5 text-[11px] font-medium text-zinc-600 uppercase tracking-widest w-28">
                Metric
              </th>
              {symbols.map((sym) => (
                <th key={sym} className="text-right px-5 py-2.5">
                  <Link
                    href={`/stocks/${sym}`}
                    className="font-mono font-bold text-white hover:text-blue-400 transition-colors"
                  >
                    {sym}
                  </Link>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {metrics.map(({ label, get }) => (
              <tr key={label} className="border-b border-zinc-800/40 last:border-0">
                <td className="px-5 py-2.5 text-zinc-500 text-xs">{label}</td>
                {symbols.map((_, i) => (
                  <td
                    key={i}
                    className={`px-5 py-2.5 text-right tabular-nums font-mono ${
                      label === "Day %" && datas[i]?.change_percent != null
                        ? datas[i]!.change_percent >= 0
                          ? "text-emerald-400"
                          : "text-red-400"
                        : "text-zinc-300"
                    }`}
                  >
                    {get(infos[i], datas[i])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
