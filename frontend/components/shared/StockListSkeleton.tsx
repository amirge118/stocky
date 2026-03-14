export function StockListSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className="rounded-xl border border-zinc-800 bg-zinc-900 p-5 space-y-3"
        >
          <div className="h-6 w-20 rounded bg-zinc-700" />
          <div className="h-4 w-40 rounded bg-zinc-800" />
          <div className="flex gap-4 pt-2">
            <div className="h-3 w-16 rounded bg-zinc-800" />
            <div className="h-3 w-20 rounded bg-zinc-800" />
          </div>
        </div>
      ))}
    </div>
  )
}
