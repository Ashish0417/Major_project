"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { MapPin, Calendar, Wallet, Eye, History } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { Trip } from "@/types"

// Mock data - replace with actual API calls
const mockTrips: Trip[] = [
  {
    id: "trip-1",
    destination: "Goa",
    dates: "June 15-20, 2024",
    budget: "INR 25,000",
    status: "completed",
  },
  {
    id: "trip-2",
    destination: "Manali",
    dates: "December 1-7, 2024",
    budget: "INR 35,000",
    status: "planned",
  },
  {
    id: "trip-3",
    destination: "Kerala Backwaters",
    dates: "January 10-15, 2024",
    budget: "INR 40,000",
    status: "completed",
  },
  {
    id: "trip-4",
    destination: "Rajasthan Circuit",
    dates: "March 5-12, 2025",
    budget: "INR 55,000",
    status: "in-progress",
  },
]

const statusColors = {
  completed: "bg-green-500/10 text-green-600 border-green-500/20",
  planned: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  "in-progress": "bg-amber-500/10 text-amber-600 border-amber-500/20",
}

export default function PastTripsPage() {
  const [trips] = useState<Trip[]>(mockTrips)

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground mb-2">Past Trips</h1>
        <p className="text-muted-foreground">
          View and manage your previously planned trips.
        </p>
      </div>

      {trips.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mb-4">
            <History className="w-8 h-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">
            No trips yet
          </h3>
          <p className="text-muted-foreground max-w-sm">
            Start planning your first trip with our AI assistant to see it here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {trips.map((trip, index) => (
            <motion.div
              key={trip.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="hover:shadow-lg hover:border-primary/30 transition-all duration-300">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                        <MapPin className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-foreground">
                          {trip.destination}
                        </h3>
                        <Badge
                          variant="outline"
                          className={statusColors[trip.status]}
                        >
                          {trip.status.charAt(0).toUpperCase() + trip.status.slice(1)}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-wrap gap-4 text-sm">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Calendar className="w-4 h-4" />
                      <span>{trip.dates}</span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Wallet className="w-4 h-4" />
                      <span>{trip.budget}</span>
                    </div>
                  </div>

                  <Button variant="outline" className="w-full">
                    <Eye className="w-4 h-4 mr-2" />
                    View Details
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
