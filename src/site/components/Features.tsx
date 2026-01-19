import { memo } from "react";
import { motion } from "framer-motion";
import { FeatureCard } from "./FeatureCard";
import { 
  Shield, 
  Award,
  Globe, 
  Gamepad2,
  Sparkles
} from "lucide-react";

const featureCategories = [
  {
    icon: Shield,
    title: "Moderation & Sicherheit",
    category: "moderation" as const,
    features: [
      "Ban, Kick, Mute, Warn Befehle",
      "Intelligentes Anti-Spam System",
      "Automatisches Warning-Management",
      "Detaillierte Moderation-Logs",
      "Temporäre Strafen (Timeout)",
      "Reason-Tracking für alle Actions",
    ],
  },
  {
    icon: Award,
    title: "Community Engagement",
    category: "community" as const,
    features: [
      "Vollständig anpassbares XP-System",
      "Rollenbelohnungen für Level-Ups",
      "Server & Global Leaderboards",
      "XP-Multiplikatoren & Boosts",
      "Voice-Channel XP-Tracking",
      "Automatische Begrüßungsnachrichten",
    ],
  },
  {
    icon: Globe,
    title: "Social & Information",
    category: "social" as const,
    features: [
      "Echtzeit-Chat mit anderen Servern",
      "Wikipedia Integration",
      "Live-Wetterinformationen",
      "Server-übergreifende Reputation",
      "Mehrsprachige Unterstützung",
      "Report & Block Funktionen",
    ],
  },
  {
    icon: Gamepad2,
    title: "Interaktive Features",
    category: "interactive" as const,
    features: [
      "Temporary Voice Channels",
      "Individuelle Kanalverwaltung",
      "Server-Statistiken in Echtzeit",
      "User-Activity Tracking",
      "Command-Usage Analytics",
      "Auto-Delete bei Inaktivität",
    ],
  },
];

export const Features = memo(function Features() {
  return (
    <section id="features" className="py-32 relative overflow-hidden">
      {/* Simple Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-primary/5 to-background" />
      
      <div className="container relative z-10 px-4">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="text-center max-w-3xl mx-auto mb-20"
        >
          <div className="inline-flex items-center gap-2 glass rounded-full px-4 py-2 mb-6">
            <Sparkles className="w-4 h-4 text-accent" />
            <span className="text-sm text-foreground/70">Über 90 Befehle</span>
          </div>
          
          <h2 className="text-4xl md:text-6xl font-bold mb-6">
            <span className="text-foreground">Alles was du </span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent font-extrabold">brauchst</span>
          </h2>
          <p className="text-foreground/70 text-lg md:text-xl max-w-2xl mx-auto">
            Ein Bot für alle deine Server-Bedürfnisse. Moderation, Engagement, Social Features und mehr.
          </p>
        </motion.div>

        {/* Feature Cards Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {featureCategories.map((category, index) => (
            <FeatureCard
              key={category.title}
              icon={category.icon}
              title={category.title}
              features={category.features}
              category={category.category}
              delay={index * 0.1}
            />
          ))}
        </div>
      </div>
    </section>
  );
});
