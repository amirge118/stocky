export default function Loading() {
  return (
    <div className="min-h-screen bg-zinc-950 p-4">
      <div className="max-w-5xl mx-auto space-y-6 animate-pulse">
        <div className="h-8 w-48 rounded bg-zinc-800" />
        <div className="h-12 w-64 rounded bg-zinc-800" />
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="space-y-2">
                <div className="h-3 w-16 rounded bg-zinc-700" />
                <div className="h-6 w-24 rounded bg-zinc-700" />
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
          <div className="h-4 w-32 rounded bg-zinc-700 mb-4" />
          <div className="space-y-3">
            {[0, 1, 2, 3, 4].map((i) => (
              <div key={i} className="h-14 rounded bg-zinc-800" />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
