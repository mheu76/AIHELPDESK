"use client"

import { useEffect, useState } from "react"
import { adminApi, DashboardStats } from "@/lib/api"

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      setLoading(true)
      const data = await adminApi.getDashboard()
      setStats(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard")
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-8">Loading dashboard...</div>
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    )
  }

  if (!stats) {
    return null
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">System Overview</h2>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard title="Total Users" value={stats.total_users} />
        <StatCard title="Active Users" value={stats.active_users} />
        <StatCard title="Chat Sessions" value={stats.total_sessions} />
        <StatCard title="Total Tickets" value={stats.total_tickets} />
        <StatCard title="KB Documents" value={stats.total_kb_documents} />
        <StatCard
          title="LLM Provider"
          value={stats.llm_provider.toUpperCase()}
          valueClass="text-blue-600"
        />
      </div>

      {/* Recent Activities */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Activities</h3>
        </div>
        <div className="p-6">
          {stats.recent_activities.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No recent activities</p>
          ) : (
            <div className="space-y-4">
              {stats.recent_activities.map((activity, idx) => (
                <div key={idx} className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className="w-2 h-2 mt-2 rounded-full bg-blue-500" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">{activity.description}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {activity.user_name} • {new Date(activity.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({
  title,
  value,
  valueClass = "text-gray-900"
}: {
  title: string
  value: string | number
  valueClass?: string
}) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-sm font-medium text-gray-500 mb-2">{title}</h3>
      <p className={`text-3xl font-bold ${valueClass}`}>{value}</p>
    </div>
  )
}
