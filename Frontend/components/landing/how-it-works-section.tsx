"use client"

import { motion } from "framer-motion"

const steps = [
  {
    number: "01",
    title: "Create Your Profile",
    description: "Tell us about your travel preferences, budget, and the experiences you love most.",
  },
  {
    number: "02",
    title: "Chat with AI",
    description: "Describe your dream trip in natural language. Our AI understands context and nuance.",
  },
  {
    number: "03",
    title: "Review Itineraries",
    description: "Get multiple personalized itineraries to choose from, each tailored to your preferences.",
  },
  {
    number: "04",
    title: "Refine & Enjoy",
    description: "Provide feedback to fine-tune recommendations and make your next trip even better.",
  },
]

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <motion.span
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-primary font-medium text-sm uppercase tracking-wider"
          >
            How It Works
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="mt-3 text-3xl sm:text-4xl font-bold text-foreground text-balance"
          >
            Four simple steps to your perfect trip
          </motion.h2>
        </div>

        <div className="relative">
          {/* Connecting line */}
          <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-0.5 bg-border -translate-y-1/2" />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step, index) => (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="relative"
              >
                <div className="bg-card rounded-2xl p-6 border border-border relative z-10">
                  <span className="text-5xl font-bold text-primary/20 mb-4 block">
                    {step.number}
                  </span>
                  <h3 className="text-xl font-semibold text-foreground mb-2">
                    {step.title}
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {step.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
