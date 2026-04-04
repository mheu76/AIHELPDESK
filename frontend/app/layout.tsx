import type { Metadata } from "next"
import { AuthProvider } from "@/components/auth-provider"
import "./globals.css"

export const metadata: Metadata = {
  title: "IT AI 헬프데스크",
  description: "AI 기반 사내 IT 지원 시스템",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-50">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
