import { memo } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Shield, Heart, Github, MessageCircle, ExternalLink, Terminal, Sparkles, Code2 } from "lucide-react";

const socialLinks = [
  { icon: Github, href: "https://github.com/ManagerX-Development/ManagerX", label: "GitHub" },
  { icon: MessageCircle, href: "https://discord.gg/dein-link", label: "Discord Support" },
];

export const Footer = memo(function Footer() {
  return (
    <footer className="relative py-24 border-t border-white/5 bg-background overflow-hidden">
      {/* Hintergrund-Effekte */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-[1px] bg-gradient-to-r from-transparent via-primary/20 to-transparent" />
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-primary/5 blur-[120px] rounded-full pointer-events-none" />
      
      <div className="container relative z-10 px-4">
        <div className="flex flex-col items-center">
          
          {/* --- HERO LOGO REPLICA --- */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
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

          {/* --- BRAND TITLE --- */}
          <motion.h2
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-5xl md:text-6xl font-bold mb-6 tracking-tight text-center"
          >
            <span className="text-foreground italic">Manager</span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent ml-2">X</span>
          </motion.h2>

          {/* --- SLOGAN --- */}
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-lg md:text-xl text-muted-foreground mb-16 font-medium tracking-tight"
          >
            Sicher <span className="text-primary/40 mx-2">•</span> 
            Schnell <span className="text-primary/40 mx-2">•</span> 
            Open Source
          </motion.p>

          {/* --- SOCIAL BUTTONS --- */}
          <div className="flex flex-wrap justify-center gap-4 mb-20">
            {socialLinks.map((link) => (
              <motion.a
                key={link.label}
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
                whileHover={{ y: -4 }}
                className="glass px-10 py-4 rounded-2xl border border-white/5 flex items-center gap-3 text-sm font-bold hover:bg-white/5 transition-all shadow-xl shadow-black/20"
              >
                <link.icon className="w-5 h-5 text-primary" />
                {link.label}
              </motion.a>
            ))}
          </div>

          {/* --- NAVIGATION & TECH GRID --- */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-12 text-center md:text-left border-y border-white/5 py-16 w-full max-w-6xl mb-16">
            
            {/* Spalte 1: Bot Navigation */}
            <div className="flex flex-col gap-4">
              <span className="text-[10px] font-black uppercase tracking-widest text-primary">Schnellzugriff</span>
              <a href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Features</a>
              <a href="#stats" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Stats</a>
              <a href="#commands" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Commands</a>
            </div>

            {/* Spalte 2: Links */}
            <div className="flex flex-col gap-4">
              <span className="text-[10px] font-black uppercase tracking-widest text-primary">Links</span>
              <a href="https://docs.oppro-network.de/" target="_blank" rel="noreferrer" className="text-sm text-muted-foreground hover:text-foreground flex items-center justify-center md:justify-start gap-1">
                Docs <ExternalLink className="w-3 h-3" />
              </a>
              <a href="https://discord.com" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Invite Bot</a>
              <a href="https://status.oppro-network.de" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Status Page</a>
            </div>

            {/* Spalte 3: Rechtliches */}
            <div className="flex flex-col gap-4">
              <span className="text-[10px] font-black uppercase tracking-widest text-primary">Rechtliches</span>
              <Link to="/datenschutz" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Datenschutz</Link>
              <Link to="/impressum" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Impressum</Link>
              <Link to="/nutzungsbedingungen" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Nutzungsbedingungen</Link>
            </div>

            {/* Spalte 4: TECH STACK (DEINE REPO DATEN) */}
            <div className="flex flex-col gap-4">
              <span className="text-[10px] font-black uppercase tracking-widest text-primary">System Architecture</span>
              <div className="space-y-4">
                {/* Python */}
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[10px] font-mono tracking-tighter">
                    <span className="text-foreground">Python (Core)</span>
                    <span className="text-primary">66.6%</span>
                  </div>
                  <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      whileInView={{ width: "66.6%" }}
                      viewport={{ once: true }}
                      className="h-full bg-primary shadow-[0_0_8px_rgba(var(--primary),0.4)]" 
                    />
                  </div>
                </div>

                {/* TypeScript */}
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[10px] font-mono tracking-tighter">
                    <span className="text-foreground">TypeScript (Web)</span>
                    <span className="text-accent">32.0%</span>
                  </div>
                  <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      whileInView={{ width: "32.0%" }}
                      viewport={{ once: true }}
                      className="h-full bg-accent shadow-[0_0_8px_rgba(var(--accent),0.4)]" 
                    />
                  </div>
                </div>

                <div className="flex items-center gap-3 pt-1">
                  <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-400 opacity-50" />
                    <span className="text-[9px] font-mono text-muted-foreground">CSS 1.1%</span>
                  </div>
                  <div className="flex items-center gap-2 px-2 py-0.5 rounded bg-accent/5 border border-accent/10">
                    <Terminal className="w-3 h-3 text-accent" />
                    <span className="text-[9px] font-mono text-accent">V2.0.0</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* --- BOTTOM BAR --- */}
          <div className="flex flex-col md:flex-row items-center justify-between w-full gap-8">
            <div className="flex items-center gap-3 text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground">
              <span>Built with</span>
              <Heart className="w-4 h-4 text-primary fill-primary animate-pulse" />
              <span>by ManagerX Dev Team</span>
            </div>

            <div className="flex items-center gap-6 opacity-40">
              <div className="flex items-center gap-2 text-[10px] font-mono uppercase">
                <Code2 className="w-3 h-3" />
                <span>Open Source Project</span>
              </div>
            </div>

            <p className="text-[10px] font-mono text-muted-foreground/40">
              © {new Date().getFullYear()} / ALL RIGHTS RESERVED
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
});