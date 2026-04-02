"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { GlobalStockSearch } from "@/components/GlobalStockSearch"
import { useKeyboardNav } from "@/lib/hooks/useKeyboardNav"

const NAV_LINKS = [
  { href: "/portfolio", label: "Portfolio", shortcut: "P" },
  { href: "/watchlist", label: "Watchlist", shortcut: "W" },
  { href: "/market",    label: "Market",    shortcut: "M" },
  { href: "/agents",    label: "Agents",    shortcut: null },
  { href: "/settings",  label: "Settings",  shortcut: null },
]

export function Navbar() {
  const pathname = usePathname()
  useKeyboardNav()

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
          {NAV_LINKS.map(({ href, label, shortcut }) => {
            const active = isActive(href)
            return (
              <Link
                key={href}
                href={href}
                title={shortcut ? `${label} (${shortcut})` : label}
                className={`
                  relative px-3 py-1.5 rounded-md text-sm font-medium transition-colors
                  flex items-center gap-1.5
                  ${active
                    ? "text-electric-400 bg-electric-500/10 border border-electric-500/20 rounded-lg"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
                  }
                `}
              >
                {label}
                {shortcut && (
                  <span className="hidden lg:inline-flex items-center justify-center w-4 h-4 rounded text-[9px] font-bold text-zinc-600 bg-zinc-800 border border-zinc-700">
                    {shortcut}
                  </span>
                )}
              </Link>
            )
          })}
        </div>

        {/* Global Search */}
        <div className="ml-auto flex items-center gap-2">
          <kbd className="hidden lg:inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-medium text-zinc-500 bg-zinc-800 border border-zinc-700 rounded">
            <span className="text-[11px]">⌘</span>K
          </kbd>
          <GlobalStockSearch />
        </div>
      </div>
    </nav>
  )
}
