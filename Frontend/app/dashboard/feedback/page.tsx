"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { MessageCircle, MapPin, Calendar, Send, Loader2, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { toast } from "sonner"
import { submitFeedback, getUserIdFromToken, getUserTrips } from "@/lib/api"
import type { Trip } from "@/types"

export default function FeedbackPage() {
  const [selectedTrip, setSelectedTrip] = useState<string | null>(null)
  const [feedback, setFeedback] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submittedTrips, setSubmittedTrips] = useState<string[]>([])
  
  const [pastTrips, setPastTrips] = useState<Trip[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    getUserTrips().then(data => {
      setPastTrips(data)
    }).catch(err => {
      console.error(err)
    }).finally(() => {
      setIsLoading(false)
    })
  }, [])

  const handleSubmit = async () => {
    if (!selectedTrip || !feedback.trim()) {
      toast.error("Please select a trip and provide feedback")
      return
    }

    setIsSubmitting(true)

    try {
      const userId = getUserIdFromToken() || "anonymous"
      await submitFeedback({
        user_id: userId,
        trip_id: selectedTrip,
        feedback: feedback.trim(),
      })

      toast.success("Feedback submitted successfully!", {
        description: "Your feedback helps us improve your future recommendations.",
      })

      setSubmittedTrips([...submittedTrips, selectedTrip])
      setSelectedTrip(null)
      setFeedback("")
    } catch (error) {
      toast.error("Failed to submit feedback. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground mb-2">Trip Feedback</h1>
        <p className="text-muted-foreground">
          Share your experience to help us personalize your future trip recommendations.
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center p-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : pastTrips.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <h3 className="text-lg font-semibold text-foreground mb-2">
              No Trips Yet
            </h3>
            <p className="text-muted-foreground">
              You haven't planned any trips yet! Start chatting with our AI to build an itinerary.
            </p>
          </CardContent>
        </Card>
      ) : (
      <div className="grid gap-6">
        {/* Trip Selection */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-foreground">
              Select a Trip
            </h2>
            <p className="text-sm text-muted-foreground">
              Choose a trip you would like to provide feedback for.
            </p>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3">
              {pastTrips.map((trip, index) => {
                const isSubmitted = submittedTrips.includes(trip.id)
                const isSelected = selectedTrip === trip.id

                return (
                  <motion.button
                    key={trip.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    onClick={() => !isSubmitted && setSelectedTrip(trip.id)}
                    disabled={isSubmitted}
                    className={`flex items-center gap-4 p-4 rounded-xl border transition-all text-left ${
                      isSubmitted
                        ? "bg-muted/50 border-border opacity-60 cursor-not-allowed"
                        : isSelected
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/30 hover:bg-muted/50"
                    }`}
                  >
                    <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                      {isSubmitted ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : (
                        <MapPin className="w-5 h-5 text-primary" />
                      )}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium text-foreground">
                        {trip.destination}
                      </h3>
                      <div className="flex items-center gap-1.5 text-sm text-muted-foreground mt-0.5">
                        <Calendar className="w-3.5 h-3.5" />
                        <span>{trip.dates}</span>
                      </div>
                    </div>
                    {isSubmitted && (
                      <span className="text-xs text-green-600 font-medium">
                        Feedback Submitted
                      </span>
                    )}
                  </motion.button>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Feedback Form */}
        {selectedTrip && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <MessageCircle className="w-5 h-5 text-primary" />
                  Your Feedback
                </h2>
                <p className="text-sm text-muted-foreground">
                  Tell us about your experience. What did you enjoy? What could be improved?
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="The trip was amazing! The hotel recommendations were spot on. However, the itinerary felt a bit rushed on day 3. I would have loved more time at the beach..."
                  className="min-h-[150px] resize-none"
                />

                <div className="bg-muted/50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-foreground mb-2">
                    Tips for helpful feedback:
                  </h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>- Mention what you loved about the trip</li>
                    <li>- Share if the budget estimates were accurate</li>
                    <li>- Tell us if the pace felt right</li>
                    <li>- Suggest what could be improved</li>
                  </ul>
                </div>

                <Button
                  onClick={handleSubmit}
                  disabled={!feedback.trim() || isSubmitting}
                  className="w-full"
                >
                  {isSubmitting ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      <Send className="w-5 h-5 mr-2" />
                      Submit Feedback
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Empty state when no trip selected */}
        {!selectedTrip && pastTrips.every(t => submittedTrips.includes(t.id)) && (
          <Card>
            <CardContent className="py-12 text-center">
              <div className="w-16 h-16 rounded-2xl bg-green-500/10 flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                All feedback submitted!
              </h3>
              <p className="text-muted-foreground">
                Thank you for helping us improve. Your future recommendations will be even better.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
      )}
    </div>
  )
}
