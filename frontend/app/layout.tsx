import type { Metadata } from "next"
import { Inter, JetBrains_Mono } from "next/font/google"
import dynamic from "next/dynamic"
import { Navbar } from "@/components/Navbar"
import { Providers } from "@/lib/providers"
import "@/styles/globals.css"

const AlertNotifier = dynamic(() => import("@/components/AlertNotifier"), { ssr: false })

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
  fallback: ["system-ui", "arial"],
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-mono",
  weight: ["400", "500", "600"],
})

export const metadata: Metadata = {
  title: "Stocky — Financial Intelligence Platform",
  description: "Portfolio tracking, AI-powered analysis, and real-time price alerts.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans`}>
        <Providers>
          <AlertNotifier />
          <Navbar />
          {children}
        </Providers>
      </body>
    </html>
  )
}
