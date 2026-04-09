import type { NextRequest } from "next/server"
import { NextResponse } from "next/server"

/** Belt-and-suspenders with next.config redirects: legacy routes land on home. */
export function middleware(request: NextRequest) {
  const p = request.nextUrl.pathname
  if (p === "/market" || p.startsWith("/market/")) {
    const url = request.nextUrl.clone()
    url.pathname = "/"
    url.search = ""
    return NextResponse.redirect(url, 308)
  }
  if (p === "/stocks" || p === "/stocks/compare") {
    const url = request.nextUrl.clone()
    url.pathname = "/"
    url.search = ""
    return NextResponse.redirect(url, 308)
  }
  return NextResponse.next()
}

export const config = {
  matcher: ["/market", "/market/:path*", "/stocks", "/stocks/compare"],
}
