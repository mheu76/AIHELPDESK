"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!token) {
      router.push("/auth/login")
      return
    }

    const userStr = localStorage.getItem("user")
    if (userStr) {
      const userData = JSON.parse(userStr)
      if (userData.role !== "admin") {
        alert("Access denied. Admin only.")
        router.push("/chat")
        return
      }
      setUser(userData)
    }
    setLoading(false)
  }, [router])

  if (loading) {
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
    <div className="min-h-screen bg-gray-50">
      {/* Admin Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <h1 className="text-xl font-bold text-gray-900">Admin Dashboard</h1>
              <nav className="flex space-x-4">
                <Link
                  href="/admin"
                  className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Dashboard
                </Link>
                <Link
                  href="/admin/users"
                  className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Users
                </Link>
                <Link
                  href="/admin/settings"
                  className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Settings
                </Link>
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/chat"
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                Back to Chat
              </Link>
              <div className="text-sm text-gray-600">
                {user.full_name} ({user.role})
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  )
}
