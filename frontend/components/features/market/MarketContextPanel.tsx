/**
 * Static reference for interpreting the snapshot (not personalized advice).
 */
export function MarketContextPanel() {
  return (
    <section
      className="rounded-xl border border-zinc-800 bg-zinc-950/50 px-4 py-4"
      aria-labelledby="market-context-heading"
    >
      <h2
        id="market-context-heading"
        className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-3"
      >
        Reading this snapshot
      </h2>
      <ul className="space-y-2 text-sm text-zinc-400 leading-relaxed list-disc pl-4">
        <li>
          <span className="text-zinc-300">Benchmarks</span> (e.g. SPY, QQQ, DIA, IWM) show broad
          large-cap, growth-heavy, blue-chip, and small-cap direction in one glance.
        </li>
        <li>
          <span className="text-zinc-300">Top movers</span> below are drawn from a fixed mega-cap
          universe for the session — useful for breadth, not a full market scan.
        </li>
        <li>
          When sector ETF tiles are available, use them for{" "}
          <span className="text-zinc-300">rotation</span> clues; click a tile for sector headlines.
        </li>
        <li>
          Implied volatility benchmarks (e.g. VIX) are not shown here; pair price action with your
          own risk and news workflow.
        </li>
      </ul>
      <p className="mt-4 text-[11px] text-zinc-600 leading-relaxed border-t border-zinc-800/80 pt-3">
        Informational only — not investment advice. Quotes are delayed and depend on upstream data
        providers.
      </p>
    </section>
  )
}
