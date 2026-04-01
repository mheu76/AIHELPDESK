"use client"

import { useEffect, useState } from "react"
import { adminApi, SystemSettings } from "@/lib/api"

export default function SettingsPage() {
  const [settings, setSettings] = useState<SystemSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [editData, setEditData] = useState<Partial<SystemSettings>>({})

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      setLoading(true)
      const data = await adminApi.getSettings()
      setSettings(data)
      setEditData(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || "Failed to load settings")
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      setSuccess(false)
      const updated = await adminApi.updateSettings(editData)
      setSettings(updated)
      setEditData(updated)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err: any) {
      setError(err.message || "Failed to save settings")
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    if (settings) {
      setEditData(settings)
    }
  }

  if (loading) {
    return <div className="text-center py-8">Loading settings...</div>
  }

  if (error && !settings) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">System Settings</h2>
        {success && (
          <div className="bg-green-50 text-green-700 px-4 py-2 rounded-md text-sm">
            Settings saved successfully
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* LLM Settings */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          LLM Configuration
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              LLM Provider
            </label>
            <select
              value={editData.llm_provider || ""}
              onChange={(e) => setEditData({ ...editData, llm_provider: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="claude">Claude (Anthropic)</option>
              <option value="openai">OpenAI</option>
            </select>
            <p className="mt-1 text-xs text-gray-500">
              Changes apply immediately to new requests
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Model Name
            </label>
            <input
              type="text"
              value={editData.llm_model || ""}
              onChange={(e) => setEditData({ ...editData, llm_model: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="claude-sonnet-4-20250514"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Temperature: {editData.llm_temperature?.toFixed(2) || "0.70"}
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={editData.llm_temperature || 0.7}
              onChange={(e) => setEditData({ ...editData, llm_temperature: parseFloat(e.target.value) })}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Focused (0.0)</span>
              <span>Balanced (1.0)</span>
              <span>Creative (2.0)</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Tokens
            </label>
            <input
              type="number"
              value={editData.max_tokens || 1024}
              onChange={(e) => setEditData({ ...editData, max_tokens: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              min="1"
              max="100000"
            />
          </div>
        </div>
      </div>

      {/* RAG Settings */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          RAG Configuration
        </h3>
        <div className="space-y-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={editData.rag_enabled ?? true}
              onChange={(e) => setEditData({ ...editData, rag_enabled: e.target.checked })}
              className="mr-2"
            />
            <label className="text-sm font-medium text-gray-700">
              Enable RAG (Retrieval-Augmented Generation)
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Top K Documents
            </label>
            <input
              type="number"
              value={editData.rag_top_k || 3}
              onChange={(e) => setEditData({ ...editData, rag_top_k: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              min="1"
              max="20"
            />
            <p className="mt-1 text-xs text-gray-500">
              Number of relevant documents to retrieve
            </p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3">
        <button
          onClick={handleReset}
          className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Reset
        </button>
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save Settings"}
        </button>
      </div>
    </div>
  )
}
