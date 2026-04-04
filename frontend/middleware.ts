import type { NextRequest } from "next/server"
import { NextResponse } from "next/server"

/** Belt-and-suspenders: old bookmarks to /market always land on home (same as next.config redirects). */
export function middleware(request: NextRequest) {
  if (request.nextUrl.pathname === "/market" || request.nextUrl.pathname.startsWith("/market/")) {
    const url = request.nextUrl.clone()
    url.pathname = "/"
    url.search = ""
    return NextResponse.redirect(url, 308)
  }
  return NextResponse.next()
}

export const config = {
  matcher: ["/market", "/market/:path*"],
}
