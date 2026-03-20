"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { GlobalStockSearch } from "@/components/GlobalStockSearch"

const NAV_LINKS = [
  { href: "/portfolio", label: "Portfolio" },
  { href: "/watchlist", label: "Watchlist" },
  { href: "/market",    label: "Market" },
  { href: "/agents",    label: "Agents" },
]

export function Navbar() {
  const pathname = usePathname()

  const isActive = (href: string) =>
    pathname === href ||
    (href !== "/portfolio" && href !== "/watchlist" && href !== "/agents" && pathname.startsWith(href + "/")) ||
    (href === "/watchlist" && pathname.startsWith("/watchlist"))

  return (
    <nav className="glass-heavy border-b border-white/[0.06] sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-4 h-13 flex items-center gap-8">
        {/* Logo */}
        <Link
          href="/"
          className="text-sm font-bold text-white tracking-tight hover:text-zinc-300 transition-colors shrink-0"
        >
          Stocky
        </Link>

        {/* Divider */}
        <span className="h-4 w-px bg-zinc-700 shrink-0" />

        {/* Links */}
        <div className="flex items-center gap-1">
          {NAV_LINKS.map(({ href, label }) => {
            const active = isActive(href)
            return (
              <Link
                key={href}
                href={href}
                className={`
                  relative px-3 py-1.5 rounded-md text-sm font-medium transition-colors
                  ${active
                    ? "text-electric-400 bg-electric-500/10 border border-electric-500/20 rounded-lg"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
                  }
                `}
              >
                {label}
              </Link>
            )
          })}
        </div>

        {/* Global Search */}
        <div className="ml-auto">
          <GlobalStockSearch />
        </div>
      </div>
    </nav>
  )
}
