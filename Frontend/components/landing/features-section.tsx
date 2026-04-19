"use client"

import { motion } from "framer-motion"
import { Sparkles, MapPin, CreditCard, Clock, Heart, Shield } from "lucide-react"

const features = [
  {
    icon: Sparkles,
    title: "AI-Powered Planning",
    description: "Our intelligent AI analyzes your preferences to create personalized travel experiences tailored just for you.",
  },
  {
    icon: MapPin,
    title: "Smart Destinations",
    description: "Discover hidden gems and popular spots based on your travel style, whether you seek adventure or relaxation.",
  },
  {
    icon: CreditCard,
    title: "Budget Optimization",
    description: "Get the most out of your travel budget with smart recommendations that match your spending preferences.",
  },
  {
    icon: Clock,
    title: "Time-Efficient",
    description: "Generate complete itineraries in seconds, not hours. More time planning fun, less time planning logistics.",
  },
  {
    icon: Heart,
    title: "Personalized Experience",
    description: "The more you use Wanderly, the better it understands you. Your feedback shapes future recommendations.",
  },
  {
    icon: Shield,
    title: "Trusted Information",
    description: "All recommendations are verified and up-to-date, ensuring you get accurate information for your trip.",
  },
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

export function FeaturesSection() {
  return (
    <section id="features" className="py-24 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <motion.span
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-primary font-medium text-sm uppercase tracking-wider"
          >
            Features
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="mt-3 text-3xl sm:text-4xl font-bold text-foreground text-balance"
          >
            Everything you need to plan the perfect trip
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto"
          >
            Powerful features designed to make travel planning effortless and enjoyable.
          </motion.p>
        </div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
        >
          {features.map((feature) => (
            <motion.div
              key={feature.title}
              variants={itemVariants}
              className="bg-card rounded-2xl p-6 border border-border hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300"
            >
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                <feature.icon className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                {feature.title}
              </h3>
              <p className="text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
