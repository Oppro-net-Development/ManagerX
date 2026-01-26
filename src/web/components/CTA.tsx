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
      {/* Premium Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-primary/8 to-accent/5" />
      <div className="absolute top-1/2 left-1/4 w-[500px] h-[500px] bg-primary/10 blur-[150px] rounded-full" />
      <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-accent/10 blur-[150px] rounded-full" />

      <div className="container relative z-10 px-4">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
          className="glass rounded-[2.5rem] p-10 md:p-24 text-center max-w-5xl mx-auto border border-white/10 backdrop-blur-lg shadow-2xl"
        >
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1, duration: 0.6, ease: "easeInOut" }}
            className="inline-flex items-center gap-2 glass rounded-full px-6 py-3 mb-10 border border-accent/20"
          >
            <Sparkles className="w-4 h-4 text-accent animate-spin" style={{animationDuration: "3s"}} />
            <span className="text-sm text-foreground/80 font-bold">100% Kostenlos & Open Source</span>
          </motion.div>

          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2, duration: 0.7, ease: "easeInOut" }}
            className="text-5xl md:text-7xl font-black mb-8 tracking-tighter leading-tight"
          >
            <span className="text-foreground">Bereit für das </span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-primary to-accent font-black">nächste Level</span>
            <span className="text-foreground">?</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 }}
            className="text-lg md:text-2xl text-muted-foreground mb-14 max-w-3xl mx-auto leading-relaxed font-medium"
          >
            Füge ManagerX jetzt zu deinem Server hinzu und erlebe die moderne Discord Server-Verwaltung mit 90 innovativen Slash-Commands.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.4 }}
            className="flex flex-col sm:flex-row gap-5 justify-center mb-16"
          >
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.98 }}>
              <a 
                href="https://discord.com/oauth2/authorize?client_id=1368201272624287754&permissions=1669118160151&integration_type=0&scope=bot" 
                target="_blank" 
                rel="noopener noreferrer"
                className="group inline-flex items-center gap-3 px-8 py-4 rounded-2xl bg-gradient-to-r from-primary to-accent text-primary-foreground font-bold text-lg hover:shadow-2xl hover:shadow-primary/50 transition-all"
              >
                <span>Bot einladen</span>
                <ArrowRight className="w-5 h-5 group-hover:translate-x-2 transition-transform" />
              </a>
            </motion.div>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.98 }}>
              <a 
                href="https://discord.gg" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl glass hover:bg-white/10 border border-white/20 font-bold text-lg transition-all"
              >
                Support Server
              </a>
            </motion.div>
          </motion.div>

          {/* Bottom Stats */}
          <motion.div 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.5 }}
            className="flex flex-wrap justify-center gap-8 md:gap-16 pt-10 border-t border-white/10"
          >
            {stats.map((stat, idx) => (
              <motion.div 
                key={stat.label}
                whileHover={{ y: -5 }}
                className="text-center"
              >
                <div className="text-3xl md:text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent mb-1">
                  {stat.value}
                </div>
                <div className="text-sm text-muted-foreground font-semibold uppercase tracking-wide">
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
});
