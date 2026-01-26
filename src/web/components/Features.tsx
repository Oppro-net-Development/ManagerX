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
      {/* Premium Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-primary/5 to-accent/5" />
      <div className="absolute top-1/4 left-0 w-[600px] h-[600px] bg-primary/10 blur-[150px] rounded-full" />
      <div className="absolute bottom-1/4 right-0 w-[700px] h-[700px] bg-accent/10 blur-[150px] rounded-full" />
      
      <div className="container relative z-10 px-4">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, ease: "easeInOut" }}
          className="text-center max-w-3xl mx-auto mb-24"
        >
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: "easeInOut" }}
            className="inline-flex items-center gap-2 glass rounded-full px-6 py-3 mb-10 border border-accent/20"
          >
            <Sparkles className="w-4 h-4 text-accent animate-spin" style={{animationDuration: "3s"}} />
            <span className="text-sm text-foreground/80 font-bold">Über 90 innovative Befehle</span>
          </motion.div>
          
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1, duration: 0.7, ease: "easeInOut" }}
            className="text-5xl md:text-7xl font-black mb-8 tracking-tighter leading-tight"
          >
            <span className="text-foreground">Alles, was du </span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent font-black">wirklich brauchst</span>
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed font-medium"
          >
            Ein Bot für alle deine Server-Bedürfnisse. Moderation, Engagement, Social Features und interaktive Tools.
          </motion.p>
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
