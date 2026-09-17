"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { GlobalStockSearch } from "@/components/GlobalStockSearch"
import { useKeyboardNav } from "@/lib/hooks/useKeyboardNav"

const NAV_LINKS = [
  { href: "/portfolio", label: "Portfolio", shortcut: "P" },
  { href: "/watchlist", label: "Watchlist", shortcut: "W" },
  { href: "/earnings", label: "Earnings", shortcut: "E" },
  { href: "/settings", label: "Settings", shortcut: null },
]

export function Navbar() {
  const pathname = usePathname()
  useKeyboardNav()

  const isActive = (href: string) =>
    pathname === href ||
    (href !== "/portfolio" &&
      href !== "/watchlist" &&
      pathname.startsWith(href + "/")) ||
    (href === "/watchlist" && pathname.startsWith("/watchlist"))

  return (
    <nav className="glass-heavy sticky top-0 z-50 border-b border-white/[0.06]">
      <div className="mx-auto flex h-13 max-w-5xl items-center gap-8 px-4">
        {/* Logo */}
        <Link
          href="/"
          className="shrink-0 text-sm font-bold tracking-tight text-white transition-colors hover:text-zinc-300"
        >
          Stocky
        </Link>

        {/* Divider */}
        <span className="h-4 w-px shrink-0 bg-zinc-700" />

        {/* Links */}
        <div className="flex items-center gap-1">
          {NAV_LINKS.map(({ href, label, shortcut }) => {
            const active = isActive(href)
            return (
              <Link
                key={href}
                href={href}
                title={shortcut ? `${label} (${shortcut})` : label}
                className={`relative flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  active
                    ? "text-electric-400 bg-electric-500/10 border-electric-500/20 rounded-lg border"
                    : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
                } `}
              >
                {label}
                {shortcut && (
                  <span className="hidden h-4 w-4 items-center justify-center rounded border border-zinc-700 bg-zinc-800 text-[9px] font-bold text-zinc-600 lg:inline-flex">
                    {shortcut}
                  </span>
                )}
              </Link>
            )
          })}
        </div>

        {/* Global Search */}
        <div className="ml-auto flex items-center gap-2">
          <kbd className="hidden items-center gap-1 rounded border border-zinc-700 bg-zinc-800 px-1.5 py-0.5 text-[10px] font-medium text-zinc-500 lg:inline-flex">
            <span className="text-[11px]">⌘</span>K
          </kbd>
          <GlobalStockSearch />
        </div>
      </div>
    </nav>
  )
}
