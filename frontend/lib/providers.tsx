"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { useState } from "react"
import { Toaster } from "@/components/ui/toaster"
import { AlertChecker } from "@/components/features/stocks/AlertChecker"
import { WatchlistProvider } from "@/lib/providers/WatchlistProvider"

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      <WatchlistProvider>
        {children}
        <AlertChecker />
        <ReactQueryDevtools initialIsOpen={false} />
        <Toaster />
      </WatchlistProvider>
    </QueryClientProvider>
  )
}
