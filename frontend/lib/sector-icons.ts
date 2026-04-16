import {
  BarChart2,
  Briefcase,
  Building2,
  Cpu,
  Factory,
  HeartPulse,
  Layers,
  Lightbulb,
  MessageSquare,
  ShoppingBag,
  ShoppingCart,
  TrendingUp,
  Zap,
  type LucideIcon,
} from "lucide-react"

export const SECTOR_ICONS: Record<string, LucideIcon> = {
  "Technology": Cpu,
  "Healthcare": HeartPulse,
  "Financials": TrendingUp,
  "Energy": Zap,
  "Consumer Discretionary": ShoppingBag,
  "Consumer Staples": ShoppingCart,
  "Industrials": Factory,
  "Materials": Layers,
  "Real Estate": Building2,
  "Utilities": Lightbulb,
  "Communication Services": MessageSquare,
  "ETFs": BarChart2,
}

// Active chip: colored border + tinted background + colored text
export const SECTOR_ACTIVE_COLORS: Record<string, string> = {
  "Technology": "border-blue-500 bg-blue-600/20 text-blue-300",
  "Healthcare": "border-rose-500 bg-rose-600/20 text-rose-300",
  "Financials": "border-emerald-500 bg-emerald-600/20 text-emerald-300",
  "Energy": "border-amber-500 bg-amber-600/20 text-amber-300",
  "Consumer Discretionary": "border-fuchsia-500 bg-fuchsia-600/20 text-fuchsia-300",
  "Consumer Staples": "border-lime-500 bg-lime-600/20 text-lime-300",
  "Industrials": "border-orange-500 bg-orange-600/20 text-orange-300",
  "Materials": "border-stone-400 bg-stone-600/20 text-stone-300",
  "Real Estate": "border-sky-500 bg-sky-600/20 text-sky-300",
  "Utilities": "border-yellow-500 bg-yellow-600/20 text-yellow-300",
  "Communication Services": "border-violet-500 bg-violet-600/20 text-violet-300",
  "ETFs": "border-indigo-500 bg-indigo-600/20 text-indigo-300",
}

// Icon color when chip is inactive
export const SECTOR_ICON_COLORS: Record<string, string> = {
  "Technology": "text-blue-400",
  "Healthcare": "text-rose-400",
  "Financials": "text-emerald-400",
  "Energy": "text-amber-400",
  "Consumer Discretionary": "text-fuchsia-400",
  "Consumer Staples": "text-lime-400",
  "Industrials": "text-orange-400",
  "Materials": "text-stone-400",
  "Real Estate": "text-sky-400",
  "Utilities": "text-yellow-400",
  "Communication Services": "text-violet-400",
  "ETFs": "text-indigo-400",
}

export function getSectorIcon(sector: string): LucideIcon {
  return SECTOR_ICONS[sector] ?? Briefcase
}

export function getSectorActiveColor(sector: string): string {
  return SECTOR_ACTIVE_COLORS[sector] ?? "border-zinc-500 bg-zinc-600/20 text-zinc-300"
}

export function getSectorIconColor(sector: string): string {
  return SECTOR_ICON_COLORS[sector] ?? "text-zinc-400"
}
