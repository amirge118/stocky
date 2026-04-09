import { NextRequest, NextResponse } from "next/server"
import fs from "fs"

// /tmp is the only writable directory in serverless environments (Vercel, etc.)
const LOG_FILE = "/tmp/error-log.jsonl"

export async function POST(request: NextRequest) {
  try {
    const entry = await request.json()
    const line = JSON.stringify({ ...entry, timestamp: new Date().toISOString() }) + "\n"
    try {
      fs.appendFileSync(LOG_FILE, line)
    } catch {
      // Filesystem write failed (e.g. read-only env) — log to console and continue
      console.error("[error-log]", line.trim())
    }
    return NextResponse.json({ ok: true })
  } catch {
    return NextResponse.json({ ok: false }, { status: 500 })
  }
}
