import { memo } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Shield, Users, MessageCircle, Sparkles, Zap, Rocket, Code2, ArrowRight } from "lucide-react";

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
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
      {/* Premium Animated Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-primary/8 via-background to-accent/5" />
      
      {/* Animated gradient orbs */}
      <div className="absolute top-1/4 -left-48 w-96 h-96 bg-primary/20 rounded-full opacity-60 blur-3xl animate-pulse" />
      <div className="absolute -bottom-32 right-1/4 w-96 h-96 bg-accent/20 rounded-full opacity-60 blur-3xl animate-pulse animation-delay-2" />
      <div className="absolute top-1/2 -right-32 w-80 h-80 bg-primary/10 rounded-full opacity-40 blur-3xl" />
      
      {/* Animated Grid Pattern */}
      <div className="absolute inset-0 opacity-[0.02] animate-drift grid-pattern" />

      <div className="container relative z-10 px-4 py-20">
        <div className="text-center max-w-5xl mx-auto">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ delay: 0.1, duration: 0.7, ease: "easeInOut" }}
            className="inline-flex items-center gap-3 glass rounded-full px-6 py-3 mb-12 border border-accent/30 backdrop-blur-md"
          >
            <span className="w-2.5 h-2.5 bg-accent rounded-full animate-pulse" />
            <span className="text-sm text-foreground/90 font-bold">Version 2.0 in Development</span>
            <Sparkles className="w-4 h-4 text-accent" />
          </motion.div>

          {/* Logo */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.8, ease: "easeInOut" }}
            className="flex items-center justify-center gap-5 mb-12"
          >
            <div className="relative">
              <motion.div 
                animate={{ scale: [1, 1.02, 1] }}
                transition={{ duration: 3, repeat: Infinity }}
                className="w-28 h-28 rounded-3xl bg-gradient-to-br from-primary via-primary/80 to-accent flex items-center justify-center shadow-2xl shadow-primary/50 border border-white/20 backdrop-blur-sm"
              >
                <Shield className="w-14 h-14 text-primary-foreground" />
              </motion.div>
              <motion.div 
                animate={{ scale: [1, 1.2, 1], rotate: [0, 10, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="absolute -bottom-3 -right-3 w-10 h-10 bg-gradient-to-br from-accent to-primary rounded-full flex items-center justify-center shadow-xl shadow-accent/60 border border-white/20"
              >
                <Sparkles className="w-5 h-5 text-accent-foreground" />
              </motion.div>
            </div>
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.8, ease: "easeInOut" }}
            className="text-7xl md:text-8xl lg:text-9xl font-black mb-10 tracking-tighter leading-none"
          >
            <span className="text-foreground">Manager</span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-primary to-accent ml-2 drop-shadow-2xl">X</span>
          </motion.h1>

          {/* Slogan */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.8, ease: "easeInOut" }}
            className="text-2xl md:text-3xl text-muted-foreground mb-16 max-w-3xl mx-auto leading-relaxed font-semibold tracking-tight flex items-center justify-center gap-3 flex-wrap"
          >
            <span className="flex items-center gap-2"><Zap className="w-6 h-6 text-primary" />Sicher</span>
            <span className="text-primary/30">•</span> 
            <span className="flex items-center gap-2"><Rocket className="w-6 h-6 text-accent" />Schnell</span>
            <span className="text-primary/30">•</span> 
            <span className="flex items-center gap-2"><Code2 className="w-6 h-6 text-primary" />Open Source</span>
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.8, ease: "easeInOut" }}
            className="flex flex-col sm:flex-row gap-5 justify-center mb-20"
          >
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.98 }}>
              <a 
                href="https://discord.com/oauth2/authorize?client_id=1368201272624287754&permissions=1669118160151&integration_type=0&scope=bot" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center gap-3 px-8 py-4 rounded-2xl bg-gradient-to-r from-primary to-accent text-primary-foreground font-bold text-lg hover:shadow-2xl hover:shadow-primary/50 transition-all group"
              >
                <span>Zum Server hinzufügen</span>
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </a>
            </motion.div>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.98 }}>
              <a 
                href="#features"
                className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl glass hover:bg-white/10 border border-white/20 font-bold text-lg transition-all"
              >
                Features entdecken
              </a>
            </motion.div>
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