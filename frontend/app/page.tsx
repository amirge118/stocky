import Link from "next/link"

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-4">Stock Insight App</h1>
        <p className="text-lg text-muted-foreground mb-8">
          Financial stock analysis platform with AI-powered insights
        </p>
        <Link
          href="/portfolio"
          className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          View Stocks
        </Link>
      </div>
    </main>
  )
}
