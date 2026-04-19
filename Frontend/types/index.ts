export interface User {
  user_id: string
  name: string
  email: string
  phone: string
  travel_theme: string
  budget_tier: string
}

export interface SignupData {
  name: string
  email: string
  phone: string
  password: string
  travel_theme: string
  budget_tier: string
}

export interface LoginData {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  user_id: string
}

export interface Itinerary {
  id: string
  title: string
  destination: string
  summary: string
  budget: string
  days: number
  highlights: string[]
  details: string
  created_at: string
}

export interface Trip {
  id: string
  destination: string
  dates: string
  budget: string
  status: "completed" | "planned" | "in-progress"
  itinerary?: Itinerary
}

export interface FeedbackData {
  user_id: string
  trip_id: string
  feedback: string
}
