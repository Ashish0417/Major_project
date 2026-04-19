"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import ReactMarkdown from "react-markdown"
import { MapPin, Calendar, Wallet, Eye, History, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { Trip } from "@/types"

import { Loader2 } from "lucide-react"
import { getUserTrips } from "@/lib/api"

const statusColors: Record<string, string> = {
  completed: "bg-green-500/10 text-green-600 border-green-500/20",
  planned: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  "in-progress": "bg-amber-500/10 text-amber-600 border-amber-500/20",
}

export default function PastTripsPage() {
  const [trips, setTrips] = useState<Trip[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedTrip, setSelectedTrip] = useState<Trip | null>(null)

  useEffect(() => {
    getUserTrips().then(data => {
      setTrips(data)
    }).catch(err => {
      console.error(err)
    }).finally(() => {
      setIsLoading(false)
    })
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

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
                          className={statusColors[trip.status] || statusColors["planned"]}
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

                  <Button variant="outline" className="w-full" onClick={() => setSelectedTrip(trip)}>
                    <Eye className="w-4 h-4 mr-2" />
                    View Details
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* Details Modal */}
      <AnimatePresence>
        {selectedTrip && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedTrip(null)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="bg-card rounded-2xl shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between p-6 border-b border-border">
                <div>
                  <span className="text-xs font-medium text-primary uppercase tracking-wider">
                    Trip Details
                  </span>
                  <h2 className="text-xl font-bold text-foreground mt-1">
                    {selectedTrip.destination}
                  </h2>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSelectedTrip(null)}
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>

              <div className="p-6 overflow-y-auto max-h-[calc(85vh-180px)]">
                <div className="flex flex-wrap gap-4 mb-6">
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted">
                    <Calendar className="w-4 h-4 text-primary" />
                    <span className="text-sm">{selectedTrip.dates}</span>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted">
                    <Wallet className="w-4 h-4 text-primary" />
                    <span className="text-sm">{selectedTrip.budget}</span>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted">
                    <Badge
                      variant="outline"
                      className={statusColors[selectedTrip.status] || statusColors["planned"]}
                    >
                      {selectedTrip.status.charAt(0).toUpperCase() + selectedTrip.status.slice(1)}
                    </Badge>
                  </div>
                </div>

                <div className="prose prose-sm max-w-none">
                  {selectedTrip.itinerary ? (
                    <>
                      <h3 className="text-lg font-semibold text-foreground mb-3">
                        {selectedTrip.itinerary.title}
                      </h3>
                      <div className="prose prose-sm dark:prose-invert max-w-none text-muted-foreground leading-relaxed">
                        <ReactMarkdown>{selectedTrip.itinerary.details}</ReactMarkdown>
                      </div>
                    </>
                  ) : (
                    <div className="text-muted-foreground text-center py-8">
                      No detailed itinerary available for this trip.
                    </div>
                  )}
                </div>
              </div>

              <div className="flex justify-end p-6 border-t border-border bg-muted/20">
                <Button
                  variant="outline"
                  onClick={() => setSelectedTrip(null)}
                >
                  Close
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
