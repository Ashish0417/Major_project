"use client"

import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Send, Sparkles, Loader2, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { sendChatMessage } from "@/lib/api"
import { ItineraryCards } from "./itinerary-cards"
import { MarkdownRenderer } from "@/components/ui/markdown-renderer"
import type { Itinerary } from "@/types"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  itineraries?: Itinerary[]
  isStreaming?: boolean
}

function parseItineraries(text: string): Itinerary[] {
  // Parse itineraries from AI response
  // This is a simplified parser - adjust based on your actual API response format
  const itineraryPattern = /(?:Itinerary|Option)\s*(\d+)[:\s]+([\s\S]*?)(?=(?:Itinerary|Option)\s*\d+|$)/gi
  const matches = [...text.matchAll(itineraryPattern)]
  
  if (matches.length === 0) return []

  return matches.map((match, index) => {
    const content = match[2].trim()
    const lines = content.split("\n").filter(l => l.trim())
    
    // Extract details from the content
    const titleMatch = content.match(/(?:Title|Name)[:\s]+(.+)/i)
    const budgetMatch = content.match(/(?:Budget|Cost|Price)[:\s]+(.+)/i)
    const daysMatch = content.match(/(\d+)\s*(?:days?|nights?)/i)
    
    return {
      id: `itinerary-${index + 1}`,
      title: titleMatch ? titleMatch[1].trim() : `Itinerary ${index + 1}`,
      destination: lines[0]?.replace(/^[*-]\s*/, "").slice(0, 50) || "Destination",
      summary: lines.slice(0, 2).join(" ").replace(/^[*-]\s*/gm, "").slice(0, 150) || content.slice(0, 150),
      budget: budgetMatch ? budgetMatch[1].trim() : "Contact for pricing",
      days: daysMatch ? parseInt(daysMatch[1]) : 5,
      highlights: lines.slice(0, 5).map(l => l.replace(/^[*-]\s*/, "").slice(0, 60)),
      details: content,
      created_at: new Date().toISOString(),
    }
  })
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    const assistantMessageId = `assistant-${Date.now()}`
    let fullText = ""

    // Add empty assistant message
    setMessages((prev) => [
      ...prev,
      { id: assistantMessageId, role: "assistant", content: "", isStreaming: true },
    ])

    try {
      await sendChatMessage(userMessage.content, (text) => {
        fullText = text
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId ? { ...msg, content: text } : msg
          )
        )
      })

      // After streaming completes, parse for itineraries
      const itineraries = parseItineraries(fullText)
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId ? { ...msg, itineraries, isStreaming: false } : msg
        )
      )
    } catch (error) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: "Sorry, something went wrong. Please try again.", isStreaming: false }
            : msg
        )
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const suggestedPrompts = [
    "Plan a 5-day trip to Goa for 2 people with a budget of INR 25,000",
    "I want a relaxing weekend getaway near Delhi under INR 10,000",
    "Adventure trip to Manali for a group of 4 in December",
    "Cultural tour of Rajasthan covering Jaipur, Udaipur, and Jodhpur",
  ]

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 lg:p-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-4">
            <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6">
              <Sparkles className="w-8 h-8 text-primary" />
            </div>
            <h2 className="text-2xl font-bold text-foreground mb-2">
              Plan your next adventure
            </h2>
            <p className="text-muted-foreground max-w-md mb-8">
              Tell me where you want to go, your budget, and travel dates. I will create
              personalized itineraries just for you.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl w-full">
              {suggestedPrompts.map((prompt, index) => (
                <button
                  key={index}
                  onClick={() => setInput(prompt)}
                  className="text-left p-4 rounded-xl border border-border bg-card hover:border-primary/30 hover:bg-muted/50 transition-colors"
                >
                  <p className="text-sm text-foreground line-clamp-2">{prompt}</p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">
            <AnimatePresence initial={false}>
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className={`flex gap-4 ${
                    message.role === "user" ? "flex-row-reverse" : ""
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      message.role === "user"
                        ? "bg-primary"
                        : "bg-accent/20"
                    }`}
                  >
                    {message.role === "user" ? (
                      <User className="w-4 h-4 text-primary-foreground" />
                    ) : (
                      <Sparkles className="w-4 h-4 text-accent" />
                    )}
                  </div>
                  <div
                    className={`flex-1 max-w-[85%] ${
                      message.role === "user" ? "text-right" : "max-w-full w-full"
                    }`}
                  >
                    {message.role === "user" ? (
                      <div className="inline-block rounded-2xl px-4 py-3 bg-primary text-primary-foreground">
                        <p className="whitespace-pre-wrap text-left">{message.content}</p>
                      </div>
                    ) : (
                      <div className="flex flex-col gap-4 w-full">
                        {message.isStreaming ? (
                          <div className="space-y-4 w-full max-w-md rounded-2xl bg-muted/40 p-5 mt-2 animate-pulse border border-border/50 shadow-sm">
                            <div className="flex items-center gap-3">
                              <Loader2 className="w-5 h-5 animate-spin text-primary" />
                              <span className="text-sm font-semibold text-primary">Crafting perfect itineraries...</span>
                            </div>
                            <div className="space-y-3 mt-4">
                              <div className="h-3 bg-primary/10 rounded w-3/4"></div>
                              <div className="h-3 bg-primary/10 rounded w-full"></div>
                              <div className="h-3 bg-primary/10 rounded w-5/6"></div>
                              <div className="h-3 bg-primary/10 rounded w-1/2"></div>
                            </div>
                          </div>
                        ) : message.itineraries && message.itineraries.length > 0 ? (
                          <div className="mt-2 text-left">
                            <p className="mb-4 text-muted-foreground">I have generated {message.itineraries.length} customized itinerary options for you. Please select one to confirm your trip.</p>
                            <ItineraryCards itineraries={message.itineraries} />
                          </div>
                        ) : (
                          <div className="inline-block rounded-2xl px-4 py-3 bg-muted text-foreground text-left max-w-none w-full relative">
                            <MarkdownRenderer>{message.content}</MarkdownRenderer>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            {isLoading && messages[messages.length - 1]?.content === "" && (
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-accent" />
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-border p-4 bg-background">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="relative flex items-end gap-2 bg-muted rounded-2xl p-2">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Plan a 5 day Goa trip for 2 people with INR 25,000 in June..."
              className="flex-1 min-h-[44px] max-h-[200px] resize-none border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 px-2"
              rows={1}
            />
            <Button
              type="submit"
              size="icon"
              disabled={!input.trim() || isLoading}
              className="h-10 w-10 rounded-xl flex-shrink-0"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground text-center mt-2">
            Press Enter to send, Shift + Enter for new line
          </p>
        </form>
      </div>
    </div>
  )
}
