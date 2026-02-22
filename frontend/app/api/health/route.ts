import { getHealth } from "@/lib/api/health"
import { NextResponse } from "next/server"

export async function GET() {
  try {
    const health = await getHealth()
    return NextResponse.json(health)
  } catch {
    return NextResponse.json(
      { error: "Failed to fetch health status" },
      { status: 500 }
    )
  }
}
