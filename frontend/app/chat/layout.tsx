"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/components/auth-provider"

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/auth/login")
    }
  }, [user, isLoading, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <ChatLayoutContent user={user}>{children}</ChatLayoutContent>
  )
}

function ChatLayoutContent({
  children,
  user,
}: {
  children: React.ReactNode
  user: any
}) {
  const { logout } = useAuth()

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-900">IT AI Helpdesk</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {user.full_name} ({user.employee_id})
            </span>
            <button
              onClick={logout}
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  )
}
