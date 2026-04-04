/**
 * Short label for an in-table news link: first few words + ellipsis when truncated.
 */
export function shortNewsLinkLabel(title: string, wordLimit = 5): string {
  const normalized = title.trim().replace(/\s+/g, " ")
  if (!normalized) return "Read article"
  const words = normalized.split(" ")
  if (words.length <= wordLimit) return normalized
  return `${words.slice(0, wordLimit).join(" ")}…`
}
