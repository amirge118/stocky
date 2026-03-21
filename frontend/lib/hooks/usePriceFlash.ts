import { useRef, useState, useEffect } from "react"

/**
 * Returns a CSS class that briefly flashes green or red when `price` changes direction.
 * Uses a ref to track the previous price and resets the class after 800ms.
 */
export function usePriceFlash(price: number | null | undefined): string {
  const prevPriceRef = useRef<number | null | undefined>(undefined)
  const [flashClass, setFlashClass] = useState("")
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (price == null) return
    const prev = prevPriceRef.current
    if (prev !== undefined && prev !== null && price !== prev) {
      const cls = price > prev ? "price-flash-green" : "price-flash-red"
      // Clear existing timeout to restart animation
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
      setFlashClass("")
      // Small rAF delay to force CSS animation restart
      requestAnimationFrame(() => {
        setFlashClass(cls)
        timeoutRef.current = setTimeout(() => setFlashClass(""), 800)
      })
    }
    prevPriceRef.current = price
  }, [price])

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [])

  return flashClass
}
