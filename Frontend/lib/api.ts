import type { SignupData, LoginData, AuthResponse, FeedbackData } from "@/types"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

function getToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem("token")
}

export function setToken(token: string): void {
  localStorage.setItem("token", token)
}

export function removeToken(): void {
  localStorage.removeItem("token")
}

export function isAuthenticated(): boolean {
  return !!getToken()
}

async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {},
  useAuth = false
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }

  if (useAuth) {
    const token = getToken()
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }))
    throw new Error(error.detail || "Request failed")
  }

  return response.json()
}

export async function signup(data: SignupData): Promise<AuthResponse> {
  const response = await apiCall<AuthResponse>("/auth/signup", {
    method: "POST",
    body: JSON.stringify(data),
  })
  setToken(response.access_token)
  return response
}

export async function login(data: LoginData): Promise<AuthResponse> {
  const response = await apiCall<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  })
  setToken(response.access_token)
  return response
}

export async function logout(): Promise<void> {
  removeToken()
}

export async function sendChatMessage(
  query: string,
  onChunk: (text: string) => void
): Promise<void> {
  const token = getToken()
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify({ query }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Chat failed" }))
    throw new Error(error.detail || "Chat failed")
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error("No response body")

  const decoder = new TextDecoder()
  let text = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    text += decoder.decode(value, { stream: true })
    onChunk(text)
  }
}

export async function submitFeedback(data: FeedbackData): Promise<{ status: string }> {
  return apiCall("/api/update_feedback", {
    method: "POST",
    body: JSON.stringify(data),
  }, true)
}

export async function selectItinerary(index: number): Promise<{ status: string, message: string, strategy: string }> {
  return apiCall("/api/itinerary/select", {
    method: "POST",
    body: JSON.stringify({ index }),
  }, true)
}

export async function getUserProfile(): Promise<any> {
  return apiCall("/api/user/profile", { method: "GET" }, true)
}

export async function getUserTrips(): Promise<any[]> {
  return apiCall("/api/user/trips", { method: "GET" }, true)
}

export function getUserIdFromToken(): string | null {
  const token = getToken()
  if (!token) return null
  try {
    const payload = JSON.parse(atob(token.split(".")[1]))
    return payload.sub
  } catch {
    return null
  }
}
