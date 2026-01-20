import { memo } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Shield, Users, MessageCircle, Sparkles } from "lucide-react";

const stats = [
  { label: "Server", value: "10+", icon: Users },
  { label: "Befehle", value: "90+", icon: MessageCircle },
  { label: "Uptime", value: "99.9%", icon: Sparkles },
];

const StatCard = memo(({ stat, index }: { stat: typeof stats[0]; index: number }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: 0.6 + index * 0.1 }}
    className="glass rounded-2xl px-8 py-5 text-center min-w-[140px] hover:bg-card/80 transition-colors duration-300"
  >
    <div className="flex items-center justify-center gap-2 mb-2">
      <stat.icon className="w-5 h-5 text-accent" />
      <span className="text-3xl font-bold text-foreground">{stat.value}</span>
    </div>
    <span className="text-sm text-muted-foreground">{stat.label}</span>
  </motion.div>
));

StatCard.displayName = "StatCard";

export const Hero = memo(function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Static Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-background to-background" />
      
      {/* Simple gradient orbs */}
      <div className="absolute top-1/4 left-1/4 w-[400px] h-[400px] bg-primary/10 rounded-full opacity-50" />
      <div className="absolute bottom-1/4 right-1/4 w-[300px] h-[300px] bg-accent/10 rounded-full opacity-40" />
      
      {/* Grid Pattern */}
      <div 
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(hsl(var(--foreground)) 1px, transparent 1px),
                            linear-gradient(90deg, hsl(var(--foreground)) 1px, transparent 1px)`,
          backgroundSize: "80px 80px",
        }}
      />

      <div className="container relative z-10 px-4 py-20">
        <div className="text-center max-w-5xl mx-auto">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="inline-flex items-center gap-2 glass rounded-full px-5 py-2.5 mb-10"
          >
            <span className="w-2.5 h-2.5 bg-accent rounded-full animate-pulse" />
            <span className="text-sm text-foreground/80 font-medium">Version 2.0 in Work</span>
            <Sparkles className="w-4 h-4 text-accent" />
          </motion.div>

          {/* Logo */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="flex items-center justify-center gap-5 mb-8"
          >
            <div className="relative">
              <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-lg shadow-primary/30">
                <Shield className="w-12 h-12 text-primary-foreground" />
              </div>
              <div className="absolute -bottom-2 -right-2 w-8 h-8 bg-accent rounded-full flex items-center justify-center shadow-lg shadow-accent/30">
                <Sparkles className="w-4 h-4 text-accent-foreground" />
              </div>
            </div>
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-6xl md:text-8xl font-bold mb-8 tracking-tight"
          >
            <span className="text-foreground">Manager</span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">X</span>
          </motion.h1>

          {/* DER NEUE SLOGAN (Ersetzt die alte Description) */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-2xl md:text-3xl text-muted-foreground mb-12 max-w-3xl mx-auto leading-relaxed font-medium tracking-tight"
          >
            Sicher <span className="text-primary/40 mx-2">•</span> 
            Schnell <span className="text-primary/40 mx-2">•</span> 
            Open Source
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="flex flex-col sm:flex-row gap-5 justify-center mb-20"
          >
            <Button variant="hero" size="xl" className="group" asChild>
              <a href="https://discord.com/oauth2/authorize" target="_blank" rel="noopener noreferrer">
                <span>Zum Server hinzufügen</span>
                <span className="inline-block ml-2 group-hover:translate-x-1 transition-transform">→</span>
              </a>
            </Button>
            <Button variant="heroOutline" size="xl" asChild>
              <a href="#features">Features entdecken</a>
            </Button>
          </motion.div>

          {/* Stats */}
          <div className="flex flex-wrap justify-center gap-6 md:gap-12">
            {stats.map((stat, index) => (
              <StatCard key={stat.label} stat={stat} index={index} />
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Gradient */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent" />
    </section>
  );
});