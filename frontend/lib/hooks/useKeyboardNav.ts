import { useEffect } from "react"
import { useRouter } from "next/navigation"

/**
 * Single-key navigation shortcuts (only fires when no input/textarea/select is focused).
 * p → /portfolio  |  w → /watchlist  |  m → /market
 */
export function useKeyboardNav() {
  const router = useRouter()

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if any modifier key is held (avoid clashing with browser shortcuts)
      if (e.metaKey || e.ctrlKey || e.altKey) return
      // Skip if focus is inside an input, textarea, select, or contenteditable
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase()
      const isEditable = (e.target as HTMLElement)?.isContentEditable
      if (tag === "input" || tag === "textarea" || tag === "select" || isEditable) return

      switch (e.key.toLowerCase()) {
        case "p":
          e.preventDefault()
          router.push("/portfolio")
          break
        case "w":
          e.preventDefault()
          router.push("/watchlist")
          break
        case "m":
          e.preventDefault()
          router.push("/market")
          break
      }
    }
    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [router])
}
