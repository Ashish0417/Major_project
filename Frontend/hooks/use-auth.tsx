"use client"

import { createContext, useContext, useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { isAuthenticated, removeToken, getUserIdFromToken } from "@/lib/api"

interface AuthContextType {
  isLoggedIn: boolean
  userId: string | null
  checkAuth: () => void
  signOut: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [userId, setUserId] = useState<string | null>(null)
  const router = useRouter()

  const checkAuth = useCallback(() => {
    const authenticated = isAuthenticated()
    setIsLoggedIn(authenticated)
    setUserId(authenticated ? getUserIdFromToken() : null)
  }, [])

  const signOut = useCallback(() => {
    removeToken()
    setIsLoggedIn(false)
    setUserId(null)
    router.push("/")
  }, [router])

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  return (
    <AuthContext.Provider value={{ isLoggedIn, userId, checkAuth, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
