"use client"

import React, { createContext, useContext, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { User, loadAuthState, saveAuthState, clearAuthState } from "@/lib/auth"
import { authApi } from "@/lib/api"

interface AuthContextType {
  user: User | null
  isLoading: boolean
  login: (employeeId: string, password: string) => Promise<void>
  logout: () => void
  refreshAuth: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  // Load auth state on mount
  useEffect(() => {
    const { user: savedUser, accessToken } = loadAuthState()
    if (savedUser && accessToken) {
      setUser(savedUser)
    }
    setIsLoading(false)
  }, [])

  const login = async (employeeId: string, password: string) => {
    const response = await authApi.login(employeeId, password)
    const authState = {
      user: response.user,
      accessToken: response.access_token,
      refreshToken: response.refresh_token,
    }
    saveAuthState(authState)
    setUser(response.user)
  }

  const logout = () => {
    clearAuthState()
    setUser(null)
    router.push("/auth/login")
  }

  const refreshAuth = async () => {
    const { refreshToken } = loadAuthState()
    if (!refreshToken) {
      logout()
      return
    }

    try {
      const response = await authApi.refreshToken(refreshToken)
      const { user: currentUser } = loadAuthState()
      saveAuthState({
        user: currentUser,
        accessToken: response.access_token,
        refreshToken: refreshToken,
      })
    } catch (error) {
      logout()
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        logout,
        refreshAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth는 AuthProvider 내에서만 사용할 수 있습니다")
  }
  return context
}
