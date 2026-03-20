interface SparklineProps {
  data: number[]
  width?: number
  height?: number
  color?: string
}

export function Sparkline({ data, width = 72, height = 28, color }: SparklineProps) {
  if (data.length < 2) return null

  const W = width
  const H = height
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const isUp = data[data.length - 1] >= data[0]
  const strokeColor = color ?? (isUp ? "#16a34a" : "#dc2626")
  const fillColor = color
    ? `${color}22`
    : isUp
    ? "#16a34a22"
    : "#dc262622"

  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * W
    const y = H - ((v - min) / range) * (H - 4) - 2
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  const polyPoints = pts.join(" ")
  const fillPath = `M ${pts[0]} L ${pts.join(" L ")} L ${W},${H} L 0,${H} Z`

  return (
    <svg
      width={W}
      height={H}
      viewBox={`0 0 ${W} ${H}`}
      className="shrink-0"
      aria-hidden
    >
      <path d={fillPath} fill={fillColor} />
      <polyline
        points={polyPoints}
        fill="none"
        stroke={strokeColor}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
