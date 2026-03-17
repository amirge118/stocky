"use client"
import { useQuery } from "@tanstack/react-query"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts"
import { getStockDividends } from "@/lib/api/stocks"

interface StockDividendsProps { symbol: string }

export function StockDividends({ symbol }: StockDividendsProps) {
  const { data, isPending } = useQuery({
    queryKey: ["dividends", symbol],
    queryFn: () => getStockDividends(symbol, 5),
    staleTime: 60 * 60_000,
  })

  if (isPending) return <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-4 h-32 animate-pulse" />
  if (!data || data.dividends.length === 0) return null  // Don't show section for non-dividend stocks

  const chartData = data.dividends.map(d => ({
    date: new Date(d.t).toLocaleDateString([], { year: "2-digit", month: "short" }),
    amount: d.amount,
  }))

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white">Dividends</h3>
        {data.annual_yield != null && (
          <span className="text-xs text-zinc-400">
            Trailing yield: <span className="text-green-400 font-semibold">{data.annual_yield.toFixed(2)}%</span>
          </span>
        )}
      </div>
      <div className="h-24">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 2, right: 8, left: 0, bottom: 0 }}>
            <XAxis dataKey="date" tick={{ fill: "#71717a", fontSize: 9 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
            <YAxis tick={{ fill: "#71717a", fontSize: 9 }} axisLine={false} tickLine={false} tickFormatter={v => `$${(v as number).toFixed(2)}`} width={40} />
            <Tooltip
              contentStyle={{ backgroundColor: "#18181b", border: "1px solid #3f3f46", borderRadius: "8px", fontSize: "11px" }}
              labelStyle={{ color: "#a1a1aa" }}
              formatter={(v: number) => [`$${v.toFixed(4)}`, "Dividend"]}
            />
            <Bar dataKey="amount" fill="#22c55e" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
