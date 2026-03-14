import type { Metadata } from "next"
import { Inter } from "next/font/google"
import Link from "next/link"
import { Providers } from "@/lib/providers"
import "@/styles/globals.css"

// Configure Inter font with fallback to system fonts if Google Fonts fails
const inter = Inter({ 
  subsets: ["latin"],
  display: "swap",
  fallback: ["system-ui", "arial"],
})

export const metadata: Metadata = {
  title: "Stock Insight App",
  description: "Financial stock analysis platform with AI-powered insights",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        <Providers>
          <nav className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur sticky top-0 z-50">
            <div className="max-w-5xl mx-auto px-4 h-12 flex items-center gap-6">
              <Link href="/" className="text-sm font-bold text-white tracking-tight">
                Stocky
              </Link>
              <div className="flex items-center gap-4 text-sm text-zinc-400">
                <Link href="/stocks" className="hover:text-zinc-200 transition-colors">
                  Stocks
                </Link>
                <Link href="/stocks/compare" className="hover:text-zinc-200 transition-colors">
                  Compare
                </Link>
                <Link href="/portfolio" className="hover:text-zinc-200 transition-colors">
                  Portfolio
                </Link>
                <Link href="/agents" className="hover:text-zinc-200 transition-colors">
                  Agents
                </Link>
              </div>
            </div>
          </nav>
          {children}
        </Providers>
      </body>
    </html>
  )
}
