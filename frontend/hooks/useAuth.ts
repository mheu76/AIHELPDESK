import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { authApi, type User } from '@/lib/api'

interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
}

export function useAuth() {
  const router = useRouter()
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
  })

  // 토큰 가져오기
  const getTokens = useCallback(() => {
    if (typeof window === 'undefined') return null
    return {
      accessToken: localStorage.getItem('access_token'),
      refreshToken: localStorage.getItem('refresh_token'),
    }
  }, [])

  // 토큰 저장하기
  const setTokens = useCallback((accessToken: string, refreshToken: string) => {
    if (typeof window === 'undefined') return
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
  }, [])

  // 토큰 삭제하기
  const clearTokens = useCallback(() => {
    if (typeof window === 'undefined') return
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }, [])

  // 사용자 정보 로드
  const loadUser = useCallback(async () => {
    const tokens = getTokens()
    if (!tokens?.accessToken) {
      setState({ user: null, isLoading: false, isAuthenticated: false })
      return
    }

    try {
      const user = await authApi.getMe(tokens.accessToken)
      setState({ user, isLoading: false, isAuthenticated: true })
    } catch (error) {
      // 토큰이 만료되었을 수 있으므로 갱신 시도
      const refreshed = await refreshAccessToken()
      if (!refreshed) {
        setState({ user: null, isLoading: false, isAuthenticated: false })
      }
    }
  }, [getTokens])

  // 토큰 갱신
  const refreshAccessToken = useCallback(async (): Promise<boolean> => {
    const tokens = getTokens()
    if (!tokens?.refreshToken) {
      clearTokens()
      return false
    }

    try {
      const response = await authApi.refreshToken(tokens.refreshToken)
      setTokens(response.access_token, tokens.refreshToken)

      // 새 토큰으로 사용자 정보 다시 로드
      const user = await authApi.getMe(response.access_token)
      setState({ user, isLoading: false, isAuthenticated: true })
      return true
    } catch (error) {
      clearTokens()
      setState({ user: null, isLoading: false, isAuthenticated: false })
      return false
    }
  }, [getTokens, setTokens, clearTokens])

  // 로그인
  const login = useCallback(async (employeeId: string, password: string) => {
    try {
      const response = await authApi.login(employeeId, password)
      setTokens(response.access_token, response.refresh_token)
      setState({ user: response.user, isLoading: false, isAuthenticated: true })
      return { success: true, user: response.user }
    } catch (error: any) {
      return { success: false, error: error.message || '로그인에 실패했습니다' }
    }
  }, [setTokens])

  // 로그아웃
  const logout = useCallback(() => {
    clearTokens()
    setState({ user: null, isLoading: false, isAuthenticated: false })
    router.push('/auth/login')
  }, [clearTokens, router])

  // 초기 로드
  useEffect(() => {
    loadUser()
  }, [loadUser])

  // 토큰 자동 갱신 (5분마다 체크, 만료 10분 전에 갱신)
  useEffect(() => {
    if (!state.isAuthenticated) return

    const interval = setInterval(async () => {
      const tokens = getTokens()
      if (!tokens?.accessToken) {
        logout()
        return
      }

      // JWT 토큰 디코딩 (만료 시간 확인)
      try {
        const payload = JSON.parse(atob(tokens.accessToken.split('.')[1]))
        const expiresAt = payload.exp * 1000 // 초를 밀리초로 변환
        const now = Date.now()
        const tenMinutes = 10 * 60 * 1000

        // 만료 10분 전이면 토큰 갱신
        if (expiresAt - now < tenMinutes) {
          await refreshAccessToken()
        }
      } catch (error) {
        console.error('토큰 디코딩 실패:', error)
      }
    }, 5 * 60 * 1000) // 5분마다 체크

    return () => clearInterval(interval)
  }, [state.isAuthenticated, getTokens, logout, refreshAccessToken])

  return {
    user: state.user,
    isLoading: state.isLoading,
    isAuthenticated: state.isAuthenticated,
    login,
    logout,
    refreshAccessToken,
  }
}
