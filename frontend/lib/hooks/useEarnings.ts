import { useQuery } from "@tanstack/react-query"
import { getStockEarnings, getEarningsCalendar } from "@/lib/api/earnings"

export function useStockEarnings(symbol: string) {
  return useQuery({
    queryKey: ["earnings", symbol],
    queryFn: () => getStockEarnings(symbol),
    staleTime: 60 * 60 * 1000, // 1 hour
    enabled: !!symbol,
  })
}

export function useEarningsCalendar(symbols: string[]) {
  return useQuery({
    queryKey: ["earnings-calendar", symbols.sort().join(",")],
    queryFn: () => getEarningsCalendar(symbols),
    staleTime: 60 * 60 * 1000,
    enabled: symbols.length > 0,
  })
}
