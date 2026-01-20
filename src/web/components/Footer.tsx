import { memo } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Shield, Heart, Github, MessageCircle, ExternalLink, Terminal, Sparkles } from "lucide-react";

const socialLinks = [
  { icon: Github, href: "https://github.com/dein-github", label: "GitHub" },
  { icon: MessageCircle, href: "https://discord.gg/dein-link", label: "Discord Support" },
];

export const Footer = memo(function Footer() {
  return (
    <footer className="relative py-24 border-t border-white/5 bg-background overflow-hidden">
      {/* Hintergrund-Effekte */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-[1px] bg-gradient-to-r from-transparent via-primary/20 to-transparent" />
      
      <div className="container relative z-10 px-4">
        <div className="flex flex-col items-center">
          
          {/* --- EXAKT DAS LOGO AUS DER HERO --- */}
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

          {/* --- TITEL AUS DER HERO --- */}
          <motion.h2
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-5xl md:text-6xl font-bold mb-6 tracking-tight text-center"
          >
            <span className="text-foreground">Manager</span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent ml-2">X</span>
          </motion.h2>

          {/* --- DEIN SLOGAN --- */}
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

          {/* --- NAVIGATION GRID --- */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-12 text-center border-y border-white/5 py-16 w-full max-w-5xl mb-16">
            <div className="flex flex-col gap-4">
              <span className="text-[10px] font-black uppercase tracking-widest text-primary">Bot</span>
              <a href="#features" className="text-sm text-muted-foreground hover:text-foreground">Features</a>
              <a href="#stats" className="text-sm text-muted-foreground hover:text-foreground">Stats</a>
            </div>
            <div className="flex flex-col gap-4">
              <span className="text-[10px] font-black uppercase tracking-widest text-primary">Links</span>
              <a href="https://docs.oppro-network.de/" target="_blank" className="text-sm text-muted-foreground hover:text-foreground flex items-center justify-center gap-1 text-center">Docs <ExternalLink className="w-3 h-3" /></a>
              <a href="https://discord..." className="text-sm text-muted-foreground hover:text-foreground text-center">Invite</a>
            </div>
            <div className="flex flex-col gap-4">
              <span className="text-[10px] font-black uppercase tracking-widest text-primary">Rechtliches</span>
              <Link to="/Datenschutz" className="text-sm text-muted-foreground hover:text-foreground">Datenschutz</Link>
              <Link to="/Impressum" className="text-sm text-muted-foreground hover:text-foreground">Impressum</Link>
              <Link to="/Nutzungsbedingungen" className="text-sm text-muted-foreground hover:text-foreground">Nutzungsbedingungen</Link>
            </div>
            <div className="flex flex-col gap-4 items-center">
              <span className="text-[10px] font-black uppercase tracking-widest text-primary">Status</span>
              <div className="flex items-center gap-2 text-xs font-mono text-accent">
                <Terminal className="w-4 h-4" />
                <span>Online</span>
              </div>
            </div>
          </div>

          {/* --- BOTTOM BAR --- */}
          <div className="flex flex-col md:flex-row items-center justify-between w-full gap-8">
            <div className="flex items-center gap-3 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
              <span>Built with</span>
              <Heart className="w-4 h-4 text-primary fill-primary animate-pulse" />
              <span>by ManagerX Dev Team</span>
            </div>
            <p className="text-[10px] font-mono text-muted-foreground/40">
              © {new Date().getFullYear()} / V2.0.0
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
});