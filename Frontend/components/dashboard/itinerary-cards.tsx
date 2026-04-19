"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { MarkdownRenderer, CompactMarkdown } from "@/components/ui/markdown-renderer"
import { MapPin, Calendar, Wallet, ChevronRight, X, Check, Star } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { toast } from "sonner"
import type { Itinerary } from "@/types"
import { selectItinerary } from "@/lib/api"

interface ItineraryCardsProps {
  itineraries: Itinerary[]
}

export function ItineraryCards({ itineraries }: ItineraryCardsProps) {
  const [selectedItinerary, setSelectedItinerary] = useState<Itinerary | null>(null)
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)

  const [isSelecting, setIsSelecting] = useState(false)

  const handleSelect = async (itinerary: Itinerary, index: number) => {
    setIsSelecting(true)
    try {
      await selectItinerary(index)
      setSelectedIndex(index)
      toast.success(`Selected: ${itinerary.title}`, {
        description: "This itinerary has been saved to your trips in the database.",
      })
    } catch (error: any) {
      toast.error("Selection failed", {
        description: error.message || "Could not save your itinerary.",
      })
    } finally {
      setIsSelecting(false)
    }
  }

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {itineraries.map((itinerary, index) => (
          <motion.div
            key={itinerary.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card
              className={`relative overflow-hidden hover:shadow-lg transition-all duration-300 cursor-pointer group ${
                selectedIndex === index
                  ? "ring-2 ring-primary border-primary"
                  : "hover:border-primary/30"
              }`}
            >
              {selectedIndex === index && (
                <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                  <Check className="w-4 h-4 text-primary-foreground" />
                </div>
              )}
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-medium text-primary uppercase tracking-wider">
                      Option {index + 1}
                    </span>
                    <div className="text-lg font-semibold text-foreground mt-1 line-clamp-1">
                      <CompactMarkdown>{itinerary.title}</CompactMarkdown>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-sm text-muted-foreground line-clamp-2">
                  <CompactMarkdown>{itinerary.summary}</CompactMarkdown>
                </div>

                <div className="flex flex-wrap gap-3 text-sm">
                  <div className="flex items-center gap-1.5 text-muted-foreground">
                    <Calendar className="w-4 h-4" />
                    <span>{itinerary.days} days</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-muted-foreground">
                    <Wallet className="w-4 h-4 flex-shrink-0" />
                    <span className="line-clamp-1"><CompactMarkdown>{itinerary.budget}</CompactMarkdown></span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <p className="text-xs font-medium text-foreground uppercase tracking-wider">
                    Highlights
                  </p>
                  <ul className="space-y-1">
                    {itinerary.highlights.slice(0, 3).map((highlight, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                        <Star className="w-3 h-3 text-primary mt-1 flex-shrink-0" />
                        <span className="line-clamp-1"><CompactMarkdown>{highlight}</CompactMarkdown></span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="flex gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => setSelectedItinerary(itinerary)}
                  >
                    View Details
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                  <Button
                    size="sm"
                    className={`flex-1 transition-colors ${selectedIndex === index ? "bg-green-600 hover:bg-green-700 text-white" : ""}`}
                    onClick={() => handleSelect(itinerary, index)}
                    disabled={(selectedIndex !== null) || isSelecting}
                  >
                    {selectedIndex === index ? "Confirmed ✅" : "Confirm"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Details Modal */}
      <AnimatePresence>
        {selectedItinerary && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedItinerary(null)}
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
                    Itinerary Details
                  </span>
                  <h2 className="text-xl font-bold text-foreground mt-1">
                    {selectedItinerary.title}
                  </h2>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSelectedItinerary(null)}
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>

              <div className="p-6 overflow-y-auto max-h-[calc(85vh-180px)]">
                <div className="flex flex-wrap gap-4 mb-6">
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted">
                    <MapPin className="w-4 h-4 text-primary" />
                    <span className="text-sm">{selectedItinerary.destination}</span>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted">
                    <Calendar className="w-4 h-4 text-primary" />
                    <span className="text-sm">{selectedItinerary.days} days</span>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted">
                    <Wallet className="w-4 h-4 text-primary" />
                    <span className="text-sm">{selectedItinerary.budget}</span>
                  </div>
                </div>

                <div className="prose prose-sm max-w-none">
                  <h3 className="text-lg font-semibold text-foreground mb-3">
                    Full Itinerary
                  </h3>
                  <div className="text-left w-full relative">
                    <MarkdownRenderer>{selectedItinerary.details}</MarkdownRenderer>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 p-6 border-t border-border bg-muted/20">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => setSelectedItinerary(null)}
                >
                  Back to Options
                </Button>
                <Button
                  className={`flex-1 transition-colors ${
                    selectedIndex === itineraries.findIndex(i => i.id === selectedItinerary.id)
                      ? "bg-green-600 text-white hover:bg-green-700" : ""
                  }`}
                  disabled={isSelecting || selectedIndex !== null}
                  onClick={async () => {
                    const index = itineraries.findIndex(i => i.id === selectedItinerary.id)
                    await handleSelect(selectedItinerary, index)
                  }}
                >
                  {isSelecting 
                    ? "Saving..." 
                    : selectedIndex === itineraries.findIndex(i => i.id === selectedItinerary.id) 
                      ? "Confirmed ✅"
                      : selectedIndex !== null 
                        ? "Another option confirmed" 
                        : "Confirm This Itinerary"}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
