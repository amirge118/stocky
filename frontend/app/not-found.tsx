import Link from "next/link"

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-24">
      <h2 className="text-2xl font-bold mb-4">404 - Page Not Found</h2>
      <p className="text-muted-foreground mb-4">
        The page you are looking for does not exist.
      </p>
      <Link
        href="/"
        className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
      >
        Go Home
      </Link>
    </div>
  )
}
