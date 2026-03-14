"use client"

import { useState } from "react"
import { ExternalLink } from "lucide-react"
import type { StockInfoResponse } from "@/types/stock"

interface StockAboutProps {
  info: StockInfoResponse
  compact?: boolean
}

export function StockAbout({ info, compact = false }: StockAboutProps) {
  const [expanded, setExpanded] = useState(false)
  const desc = info.description ?? ""

  // Compact mode: description only (2 lines + read more). Tags+website are in page header.
  if (compact) {
    const CHARS_PER_LINE = 85
    const TWO_LINES_CHARS = CHARS_PER_LINE * 2
    const isTruncatable = desc.length > TWO_LINES_CHARS
    const displayDesc =
      isTruncatable && !expanded ? desc.slice(0, TWO_LINES_CHARS) + "…" : desc

    return (
      <div className="rounded-xl bg-zinc-900 border border-zinc-800 px-4 py-3">
        {/* Description — 2 lines + read more */}
        {desc ? (
          <div>
            <p
              className={`text-sm text-zinc-400 leading-relaxed ${
                !expanded && isTruncatable ? "line-clamp-2" : ""
              }`}
            >
              {displayDesc}
            </p>
            {isTruncatable && (
              <button
                onClick={() => setExpanded((e) => !e)}
                className="text-blue-400 hover:text-blue-300 text-xs mt-1 transition-colors"
              >
                {expanded ? "Show less" : "Read more"}
              </button>
            )}
          </div>
        ) : (
          <p className="text-sm text-zinc-500">No description available.</p>
        )}
      </div>
    )
  }

  // Full mode (used standalone if needed)
  const TRUNCATE_AT = 220
  const isTruncatable = desc.length > TRUNCATE_AT
  const displayDesc = isTruncatable && !expanded ? desc.slice(0, TRUNCATE_AT) + "…" : desc

  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-5">
      <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wide mb-3">About</h2>

      {desc ? (
        <div className="mb-4">
          <p className="text-zinc-300 text-sm leading-relaxed">{displayDesc}</p>
          {isTruncatable && (
            <button
              onClick={() => setExpanded((e) => !e)}
              className="text-blue-400 hover:text-blue-300 text-xs mt-1 transition-colors"
            >
              {expanded ? "Show less" : "Show more"}
            </button>
          )}
        </div>
      ) : (
        <p className="text-zinc-500 text-sm mb-4">No description available.</p>
      )}

      <div className="space-y-2 text-sm">
        {info.ceo && (
          <div className="flex justify-between">
            <span className="text-zinc-400">CEO</span>
            <span className="text-white">{info.ceo}</span>
          </div>
        )}
        {info.employees != null && (
          <div className="flex justify-between">
            <span className="text-zinc-400">Employees</span>
            <span className="text-white">{info.employees.toLocaleString()}</span>
          </div>
        )}
        {info.country && (
          <div className="flex justify-between">
            <span className="text-zinc-400">Country</span>
            <span className="text-white">{info.country}</span>
          </div>
        )}
        {info.sector && (
          <div className="flex justify-between">
            <span className="text-zinc-400">Sector</span>
            <span className="text-white">{info.sector}</span>
          </div>
        )}
        {info.industry && (
          <div className="flex justify-between">
            <span className="text-zinc-400">Industry</span>
            <span className="text-white">{info.industry}</span>
          </div>
        )}
        {info.website && (
          <div className="flex justify-between items-center">
            <span className="text-zinc-400">Website</span>
            <a
              href={info.website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
            >
              {info.website.replace(/^https?:\/\//, "").replace(/\/$/, "")}
              <ExternalLink size={12} />
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
