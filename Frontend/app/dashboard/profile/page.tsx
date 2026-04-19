"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { User, Mail, Phone, Compass, Wallet, Target, Clock, Heart, Users } from "lucide-react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { getUserIdFromToken } from "@/lib/api"

// Mock user data - in real app, fetch from API
const mockUserData = {
  name: "Lasya Reddy",
  email: "lasya@example.com",
  phone: "+91-9876543210",
  travel_theme: "Nature & Wildlife",
  budget_tier: "Moderate",
  // Preference weights (0-100)
  preferences: {
    cost: 30,
    time: 20,
    preference: 35,
    popularity: 15,
  },
}

const preferenceLabels = {
  cost: { label: "Budget Priority", icon: Wallet, description: "How much budget influences recommendations" },
  time: { label: "Time Efficiency", icon: Clock, description: "Preference for optimized travel times" },
  preference: { label: "Personal Match", icon: Heart, description: "Match to your stated preferences" },
  popularity: { label: "Popular Spots", icon: Users, description: "Weight given to popular destinations" },
}

export default function ProfilePage() {
  const [userId, setUserId] = useState<string | null>(null)

  useEffect(() => {
    setUserId(getUserIdFromToken())
  }, [])

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground mb-2">Profile</h1>
        <p className="text-muted-foreground">
          Your personal information and travel preferences.
        </p>
      </div>

      <div className="grid gap-6">
        {/* Personal Information */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-foreground">
                Personal Information
              </h2>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4 p-4 rounded-xl bg-muted/50">
                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-2xl font-bold text-primary">
                    {mockUserData.name.charAt(0)}
                  </span>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-foreground">
                    {mockUserData.name}
                  </h3>
                  {userId && (
                    <p className="text-sm text-muted-foreground">
                      ID: {userId.slice(0, 12)}...
                    </p>
                  )}
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="flex items-center gap-3 p-3 rounded-lg border border-border">
                  <Mail className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="text-xs text-muted-foreground">Email</p>
                    <p className="text-sm text-foreground">{mockUserData.email}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg border border-border">
                  <Phone className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="text-xs text-muted-foreground">Phone</p>
                    <p className="text-sm text-foreground">{mockUserData.phone}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Travel Preferences */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold text-foreground">
                Travel Preferences
              </h2>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="flex items-center gap-3 p-4 rounded-xl bg-primary/5 border border-primary/20">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Compass className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Travel Style</p>
                    <p className="font-medium text-foreground">{mockUserData.travel_theme}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-4 rounded-xl bg-accent/10 border border-accent/20">
                  <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center">
                    <Wallet className="w-5 h-5 text-accent" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Budget Tier</p>
                    <p className="font-medium text-foreground">{mockUserData.budget_tier}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Preference Weights */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-primary" />
                <h2 className="text-lg font-semibold text-foreground">
                  Recommendation Weights
                </h2>
              </div>
              <p className="text-sm text-muted-foreground">
                These weights influence how our AI tailors your trip recommendations.
                They automatically adjust based on your feedback.
              </p>
            </CardHeader>
            <CardContent className="space-y-6">
              {Object.entries(mockUserData.preferences).map(([key, value], index) => {
                const pref = preferenceLabels[key as keyof typeof preferenceLabels]
                return (
                  <motion.div
                    key={key}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 + index * 0.1 }}
                    className="space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <pref.icon className="w-4 h-4 text-muted-foreground" />
                        <span className="font-medium text-foreground">{pref.label}</span>
                      </div>
                      <span className="text-sm font-semibold text-primary">{value}%</span>
                    </div>
                    <Progress value={value} className="h-2" />
                    <p className="text-xs text-muted-foreground">{pref.description}</p>
                  </motion.div>
                )
              })}
            </CardContent>
          </Card>
        </motion.div>

        {/* Info Note */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <div className="bg-muted/50 rounded-xl p-4 border border-border">
            <p className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">Pro tip:</span> Your preference weights
              are automatically fine-tuned based on your trip feedback. The more feedback you provide,
              the better your recommendations become!
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
