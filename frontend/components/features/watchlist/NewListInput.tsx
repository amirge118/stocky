"use client"

import { useRef, useState } from "react"

interface NewListInputProps {
  onCommit: (name: string) => void
  onCancel: () => void
}

export function NewListInput({ onCommit, onCancel }: NewListInputProps) {
  const [value, setValue] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)

  const commit = () => {
    const trimmed = value.trim()
    if (trimmed) onCommit(trimmed)
    else onCancel()
  }

  return (
    <input
      ref={inputRef}
      autoFocus
      value={value}
      onChange={(e) => setValue(e.target.value)}
      onBlur={commit}
      onKeyDown={(e) => {
        if (e.key === "Enter") commit()
        if (e.key === "Escape") onCancel()
      }}
      placeholder="List name..."
      className="w-full px-2 py-1 text-sm bg-zinc-800 border border-zinc-600 rounded text-white placeholder:text-zinc-500 focus:outline-none focus:border-zinc-400"
    />
  )
}
