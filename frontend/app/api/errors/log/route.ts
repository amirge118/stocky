import { NextRequest, NextResponse } from "next/server"
import fs from "fs"
import path from "path"

const LOG_FILE = path.join(process.cwd(), "error-log.jsonl")

export async function POST(request: NextRequest) {
  try {
    const entry = await request.json()
    const line = JSON.stringify({ ...entry, timestamp: new Date().toISOString() }) + "\n"
    fs.appendFileSync(LOG_FILE, line)
    return NextResponse.json({ ok: true })
  } catch {
    return NextResponse.json({ ok: false }, { status: 500 })
  }
}
