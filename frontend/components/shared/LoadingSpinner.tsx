export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-12" role="status" aria-label="Loading">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" aria-hidden="true"></div>
    </div>
  )
}
