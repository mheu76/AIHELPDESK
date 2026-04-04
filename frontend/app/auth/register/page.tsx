"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { authApi, ApiError } from "@/lib/api"

export default function RegisterPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    employeeId: "",
    email: "",
    fullName: "",
    password: "",
    confirmPassword: "",
  })
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    if (formData.password !== formData.confirmPassword) {
      setError("비밀번호가 일치하지 않습니다")
      return
    }

    setIsLoading(true)

    try {
      await authApi.register({
        employee_id: formData.employeeId,
        email: formData.email,
        full_name: formData.fullName,
        password: formData.password,
      })

      router.push("/auth/login?registered=true")
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError("예기치 않은 오류가 발생했습니다")
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-white shadow-xl rounded-lg p-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">계정 생성</h1>
        <p className="text-gray-600 mt-2">IT 헬프데스크 액세스 등록</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md text-sm">
            {error}
          </div>
        )}

        <div>
          <label htmlFor="employeeId" className="block text-sm font-medium text-gray-700 mb-1">
            사번
          </label>
          <input
            id="employeeId"
            name="employeeId"
            type="text"
            required
            value={formData.employeeId}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="EMP001"
          />
        </div>

        <div>
          <label htmlFor="fullName" className="block text-sm font-medium text-gray-700 mb-1">
            이름
          </label>
          <input
            id="fullName"
            name="fullName"
            type="text"
            required
            value={formData.fullName}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="홍길동"
          />
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
            이메일
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            value={formData.email}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="hong@company.com"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
            비밀번호
          </label>
          <input
            id="password"
            name="password"
            type="password"
            required
            value={formData.password}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="비밀번호를 생성하세요"
          />
        </div>

        <div>
          <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
            비밀번호 확인
          </label>
          <input
            id="confirmPassword"
            name="confirmPassword"
            type="password"
            required
            value={formData.confirmPassword}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="비밀번호를 다시 입력하세요"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? "계정 생성 중..." : "회원가입"}
        </button>
      </form>

      <div className="mt-6 text-center">
        <p className="text-sm text-gray-600">
          이미 계정이 있으신가요?{" "}
          <Link href="/auth/login" className="text-primary-600 hover:text-primary-700 font-medium">
            로그인
          </Link>
        </p>
      </div>
    </div>
  )
}
