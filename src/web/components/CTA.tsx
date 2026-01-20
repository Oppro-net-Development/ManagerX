import { memo } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles } from "lucide-react";

const stats = [
  { label: "Aktive Server", value: "10+" },
  { label: "Befehle ausgeführt", value: "1000+" },
  { label: "Zufriedene User", value: "300+" },
];

export const CTA = memo(function CTA() {
  return (
    <section id="support" className="py-32 relative overflow-hidden">
      {/* Simple Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-primary/5 to-background" />

      <div className="container relative z-10 px-4">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="glass rounded-[2.5rem] p-10 md:p-20 text-center max-w-5xl mx-auto"
        >
          <div className="inline-flex items-center gap-2 glass rounded-full px-5 py-2.5 mb-8">
            <Sparkles className="w-4 h-4 text-accent" />
            <span className="text-sm text-foreground/80 font-medium">100% Kostenlos</span>
          </div>

          <h2 className="text-4xl md:text-6xl font-bold mb-6">
            <span className="text-foreground">Bereit für das </span>
            <span className="text-foreground font-extrabold">nächste </span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent font-extrabold">Level</span>
            <span className="text-foreground font-extrabold">?</span>
          </h2>

          <p className="text-foreground/70 text-lg md:text-xl mb-12 max-w-2xl mx-auto leading-relaxed">
            Füge ManagerX jetzt zu deinem Server hinzu und erlebe die Zukunft 
            der Discord Server-Verwaltung.
          </p>

          <div className="flex flex-col sm:flex-row gap-5 justify-center">
            <Button variant="hero" size="xl" className="group" asChild>
              <a href="https://discord.com/oauth2/authorize" target="_blank" rel="noopener noreferrer">
                <span>Bot einladen</span>
                <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </a>
            </Button>
            <Button variant="glass" size="xl" asChild>
              <a href="https://discord.gg" target="_blank" rel="noopener noreferrer">
                Support Server
              </a>
            </Button>
          </div>

          {/* Bottom Stats */}
          <div className="flex flex-wrap justify-center gap-12 mt-16 pt-8 border-t border-border/50">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-2xl font-bold text-foreground">{stat.value}</div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
});
