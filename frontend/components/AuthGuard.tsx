"use client"

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'

interface AuthGuardProps {
  children: React.ReactNode
  requireAuth?: boolean
  requireAdmin?: boolean
}

export default function AuthGuard({
  children,
  requireAuth = true,
  requireAdmin = false
}: AuthGuardProps) {
  const router = useRouter()
  const pathname = usePathname()
  const { user, isLoading, isAuthenticated } = useAuth()

  useEffect(() => {
    if (isLoading) return

    // pathname이 null인 경우 처리하지 않음
    if (!pathname) return

    // 인증이 필요한 페이지인데 로그인하지 않음
    if (requireAuth && !isAuthenticated) {
      router.push(`/auth/login?redirect=${encodeURIComponent(pathname)}`)
      return
    }

    // 관리자 권한이 필요한데 일반 사용자
    if (requireAdmin && (!user || user.role !== 'admin')) {
      router.push('/') // 홈으로 리디렉션
      return
    }

    // 로그인 페이지인데 이미 인증됨
    if (!requireAuth && isAuthenticated && pathname.startsWith('/auth')) {
      router.push('/')
      return
    }
  }, [isLoading, isAuthenticated, requireAuth, requireAdmin, user, router, pathname])

  // 로딩 중이면 스피너 표시
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          <div className="text-gray-600">로딩 중...</div>
        </div>
      </div>
    )
  }

  // 인증 필요한데 인증 안됨
  if (requireAuth && !isAuthenticated) {
    return null
  }

  // 관리자 필요한데 권한 없음
  if (requireAdmin && (!user || user.role !== 'admin')) {
    return null
  }

  return <>{children}</>
}
