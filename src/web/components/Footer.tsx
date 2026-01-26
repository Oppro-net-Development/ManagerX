import { memo } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Shield, Heart, Github, MessageCircle, ExternalLink, Terminal, Sparkles, Code2, Zap, Users, Rocket, Star, BarChart3, Lock, Info, FileCheck, Activity } from "lucide-react";

const socialLinks = [
  { icon: Github, href: "https://github.com/ManagerX-Development/ManagerX", label: "GitHub" },
  { icon: MessageCircle, href: "https://discord.gg/dein-link", label: "Discord Support" },
];

export const Footer = memo(function Footer() {
  return (
    <footer className="relative py-32 bg-background overflow-hidden">
      {/* Premium Hintergrund-Effekte */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[1px] bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
      <div className="absolute top-0 left-0 w-[400px] h-[400px] bg-primary/10 blur-[150px] rounded-full pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-accent/10 blur-[150px] rounded-full pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.15),rgba(255,255,255,0))]" />
      
      <div className="container relative z-10 px-4">
        <div className="flex flex-col items-center">
          
          {/* --- HERO LOGO REPLICA --- */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="flex items-center justify-center gap-5 mb-12"
          >
            <div className="relative">
              <motion.div 
                whileHover={{ scale: 1.05, rotate: 5 }}
                transition={{ type: "spring", stiffness: 300 }}
                className="w-28 h-28 rounded-3xl bg-gradient-to-br from-primary via-primary/80 to-accent flex items-center justify-center shadow-2xl shadow-primary/40 border border-white/10 backdrop-blur-sm"
              >
                <Shield className="w-14 h-14 text-primary-foreground" />
              </motion.div>
              <motion.div 
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="absolute -bottom-2 -right-2 w-10 h-10 bg-gradient-to-br from-accent to-primary rounded-full flex items-center justify-center shadow-xl shadow-accent/50 border border-white/10"
              >
                <Sparkles className="w-5 h-5 text-accent-foreground" />
              </motion.div>
            </div>
          </motion.div>

          {/* --- BRAND TITLE --- */}
          <motion.h2
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-6xl md:text-7xl font-black mb-6 tracking-tighter text-center bg-gradient-to-r from-foreground via-foreground to-primary bg-clip-text text-transparent"
          >
            <span className="italic">Manager</span>
            <span className="ml-2">X</span>
          </motion.h2>

          {/* --- SLOGAN --- */}
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-xl md:text-2xl text-muted-foreground mb-20 font-bold tracking-tight flex items-center gap-4 flex-wrap justify-center"
          >
            <span className="flex items-center gap-2"><Zap className="w-5 h-5 text-primary" /> Sicher</span>
            <span className="text-primary/40">•</span> 
            <span className="flex items-center gap-2"><Rocket className="w-5 h-5 text-accent" /> Schnell</span>
            <span className="text-primary/40">•</span> 
            <span className="flex items-center gap-2"><Code2 className="w-5 h-5 text-primary" /> Open Source</span>
          </motion.p>

          {/* --- SOCIAL BUTTONS --- */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-wrap justify-center gap-4 mb-24"
          >
            {socialLinks.map((link, idx) => (
              <motion.a
                key={link.label}
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
                whileHover={{ y: -6, boxShadow: "0 20px 40px rgba(var(--primary), 0.2)" }}
                whileTap={{ scale: 0.98 }}
                transition={{ delay: idx * 0.1 }}
                className="group px-8 py-4 rounded-2xl border border-primary/20 bg-primary/5 backdrop-blur-sm flex items-center gap-3 text-sm font-bold hover:bg-primary/10 transition-all shadow-lg hover:shadow-primary/20 hover:border-primary/40"
              >
                <link.icon className="w-5 h-5 text-primary group-hover:text-accent transition-colors" />
                {link.label}
              </motion.a>
            ))}
          </motion.div>

          {/* --- NAVIGATION & TECH GRID --- */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-12 text-center md:text-left border-y border-white/10 py-20 w-full max-w-6xl mb-20 backdrop-blur-sm"
          >
            
            <motion.div 
              whileHover={{ y: -5 }}
              className="flex flex-col gap-5 p-5 rounded-2xl hover:bg-white/5 transition-all"
            >
              <span className="text-[11px] font-black uppercase tracking-widest text-primary">Schnellzugriff</span>
              <a href="#features" className="text-sm text-muted-foreground hover:text-primary transition-colors font-medium flex items-center justify-center md:justify-start gap-2 group">
                <Star className="w-3.5 h-3.5 text-primary flex-shrink-0" />
                <span className="group-hover:translate-x-1 transition-transform">Features</span>
              </a>
              <a href="#stats" className="text-sm text-muted-foreground hover:text-accent transition-colors font-medium flex items-center justify-center md:justify-start gap-2 group">
                <BarChart3 className="w-3.5 h-3.5 text-accent flex-shrink-0" />
                <span className="group-hover:translate-x-1 transition-transform">Stats</span>
              </a>
              <a href="#commands" className="text-sm text-muted-foreground hover:text-primary transition-colors font-medium flex items-center justify-center md:justify-start gap-2 group">
                <Terminal className="w-3.5 h-3.5 text-primary flex-shrink-0" />
                <span className="group-hover:translate-x-1 transition-transform">Commands</span>
              </a>
            </motion.div>

            <motion.div 
              whileHover={{ y: -5 }}
              className="flex flex-col gap-5 p-5 rounded-2xl hover:bg-white/5 transition-all"
            >
              <span className="text-[11px] font-black uppercase tracking-widest text-primary">Links</span>
              <a href="https://docs.oppro-network.de/" target="_blank" rel="noopener noreferrer" className="text-sm text-muted-foreground hover:text-accent flex items-center justify-center md:justify-start gap-2 font-medium group">
                <ExternalLink className="w-3.5 h-3.5 text-accent flex-shrink-0" />
                <span className="group-hover:translate-x-1 transition-transform">Docs</span>
              </a>
              <a href="https://discord.com" className="text-sm text-muted-foreground hover:text-primary transition-colors font-medium flex items-center justify-center md:justify-start gap-2 group">
                <Users className="w-3.5 h-3.5 text-primary flex-shrink-0" />
                <span className="group-hover:translate-x-1 transition-transform">Invite Bot</span>
              </a>
              <a href="https://status.oppro-network.de" className="text-sm text-muted-foreground hover:text-accent transition-colors font-medium flex items-center justify-center md:justify-start gap-2 group">
                <Activity className="w-3.5 h-3.5 text-accent flex-shrink-0" />
                <span className="group-hover:translate-x-1 transition-transform">Status Page</span>
              </a>
            </motion.div>

            <motion.div 
              whileHover={{ y: -5 }}
              className="flex flex-col gap-5 p-5 rounded-2xl hover:bg-white/5 transition-all"
            >
              <span className="text-[11px] font-black uppercase tracking-widest text-primary">Rechtliches</span>
              <Link to="/datenschutz" className="text-sm text-muted-foreground hover:text-primary transition-colors font-medium flex items-center justify-center md:justify-start gap-2 group">
                <Lock className="w-3.5 h-3.5 text-primary flex-shrink-0" />
                <span className="group-hover:translate-x-1 transition-transform">Datenschutz</span>
              </Link>
              <Link to="/impressum" className="text-sm text-muted-foreground hover:text-accent transition-colors font-medium flex items-center justify-center md:justify-start gap-2 group">
                <Info className="w-3.5 h-3.5 text-accent flex-shrink-0" />
                <span className="group-hover:translate-x-1 transition-transform">Impressum</span>
              </Link>
              <Link to="/nutzungsbedingungen" className="text-sm text-muted-foreground hover:text-primary transition-colors font-medium flex items-center justify-center md:justify-start gap-2 group">
                <FileCheck className="w-3.5 h-3.5 text-primary flex-shrink-0" />
                <span className="group-hover:translate-x-1 transition-transform">Nutzungsbedingungen</span>
              </Link>
              <Link to="/license" className="text-sm text-muted-foreground hover:text-accent font-medium flex items-center justify-center md:justify-start gap-2 group">
                <Code2 className="w-3.5 h-3.5 text-accent flex-shrink-0" />
                <span className="group-hover:translate-x-1 transition-transform">Open Source</span>
              </Link>
            </motion.div>

            <motion.div 
              whileHover={{ y: -5 }}
              className="flex flex-col gap-5 p-5 rounded-2xl hover:bg-white/5 transition-all"
            >
              <span className="text-[11px] font-black uppercase tracking-widest text-primary">System Architecture</span>
              <div className="space-y-5">
                <div className="space-y-2">
                  <div className="flex justify-between text-[10px] font-mono tracking-tighter">
                    <span className="text-foreground font-bold">Python (Core)</span>
                    <span className="text-primary font-bold">66.6%</span>
                  </div>
                  <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      whileInView={{ width: "66.6%" }}
                      viewport={{ once: true }}
                      transition={{ duration: 1.5, ease: "easeOut" }}
                      className="h-full bg-gradient-to-r from-primary to-primary/50 shadow-[0_0_12px_rgba(var(--primary),0.5)] rounded-full" 
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-[10px] font-mono tracking-tighter">
                    <span className="text-foreground font-bold">TypeScript (Web)</span>
                    <span className="text-accent font-bold">32.0%</span>
                  </div>
                  <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      whileInView={{ width: "32.0%" }}
                      viewport={{ once: true }}
                      transition={{ duration: 1.5, ease: "easeOut", delay: 0.2 }}
                      className="h-full bg-gradient-to-r from-accent to-accent/50 shadow-[0_0_12px_rgba(var(--accent),0.5)] rounded-full" 
                    />
                  </div>
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.6)]" />
                    <span className="text-[9px] font-mono text-muted-foreground font-medium">CSS 1.1%</span>
                  </div>
                  <motion.div 
                    whileHover={{ scale: 1.05 }}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gradient-to-r from-accent/10 to-accent/5 border border-accent/20 hover:border-accent/40 transition-all"
                  >
                    <Terminal className="w-3.5 h-3.5 text-accent" />
                    <span className="text-[9px] font-mono text-accent font-bold">V2.0.0</span>
                  </motion.div>
                </div>
              </div>
            </motion.div>
          </motion.div>

          {/* --- FOOTER BOTTOM --- */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="flex flex-col md:flex-row items-center justify-between w-full gap-8 pt-8"
          >
            <motion.div 
              whileHover={{ scale: 1.05 }}
              className="flex items-center gap-3 text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground hover:text-foreground transition-colors"
            >
              <span>Built with</span>
              <Heart className="w-4 h-4 text-red-500 fill-red-500 animate-pulse" />
              <span>by ManagerX Dev Team</span>
            </motion.div>
            <motion.div 
              whileHover={{ scale: 1.05 }}
              className="flex items-center gap-3 opacity-50 text-[11px] font-mono uppercase font-bold hover:opacity-100 transition-opacity"
            >
              <Code2 className="w-3.5 h-3.5 text-primary" />
              <span>Open Source Project</span>
            </motion.div>
            <p className="text-[11px] font-mono text-muted-foreground/60 hover:text-muted-foreground/100 transition-colors font-bold">
              © {new Date().getFullYear()} / ALL RIGHTS RESERVED
            </p>
          </motion.div>
        </div>
      </div>
    </footer>
  );
});