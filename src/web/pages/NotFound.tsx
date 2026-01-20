import { useLocation, Link } from "react-router-dom";
import { useEffect } from "react";
import { motion } from "framer-motion";
import { Shield, Sparkles, Home, Terminal } from "lucide-react";
import { Button } from "@/components/ui/button";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-background">
      {/* --- ORIGINAL HERO BACKGROUND --- */}
      <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-background to-background" />
      
      {/* Simple gradient orbs */}
      <div className="absolute top-1/4 left-1/4 w-[400px] h-[400px] bg-primary/10 rounded-full opacity-50 blur-[100px]" />
      <div className="absolute bottom-1/4 right-1/4 w-[300px] h-[300px] bg-accent/10 rounded-full opacity-40 blur-[80px]" />
      
      {/* Grid Pattern */}
      <div 
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(hsl(var(--foreground)) 1px, transparent 1px),
                            linear-gradient(90deg, hsl(var(--foreground)) 1px, transparent 1px)`,
          backgroundSize: "80px 80px",
        }}
      />

      <div className="container relative z-10 px-4">
        <div className="text-center max-w-5xl mx-auto">
          
          {/* --- ORIGINAL HERO LOGO --- */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center justify-center gap-5 mb-8"
          >
            <div className="relative">
              <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-lg shadow-primary/30">
                <Shield className="w-12 h-12 text-primary-foreground" />
              </div>
              <div className="absolute -bottom-2 -right-2 w-8 h-8 bg-destructive rounded-full flex items-center justify-center shadow-lg shadow-destructive/30">
                <span className="text-[10px] font-bold text-white">404</span>
              </div>
            </div>
          </motion.div>

          {/* --- ORIGINAL HERO TITLE STYLE --- */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-6xl md:text-8xl font-bold mb-8 tracking-tight"
          >
            <span className="text-foreground italic">Error</span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent ml-3">404</span>
          </motion.h1>

          {/* --- DESCRIPTION --- */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-xl md:text-2xl text-muted-foreground mb-12 max-w-2xl mx-auto leading-relaxed"
          >
            Dieser Pfad ist im <span className="text-foreground font-medium">ManagerX</span> Netzwerk nicht registriert. Kehre zurück zur Zentrale.
          </motion.p>

          {/* --- CTA BUTTON (HERO STYLE) --- */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="flex justify-center mb-20"
          >
            <Button variant="hero" size="xl" className="group" asChild>
              <Link to="/">
                <Home className="w-5 h-5 mr-2" />
                <span>Zurück zur Home</span>
                <span className="inline-block ml-2 group-hover:translate-x-1 transition-transform">→</span>
              </Link>
            </Button>
          </motion.div>

          {/* --- TERMINAL FOOTER --- */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="inline-flex items-center gap-3 px-6 py-2 glass rounded-full border border-white/5 text-[10px] font-mono text-muted-foreground uppercase tracking-widest"
          >
            <Terminal className="w-3 h-3 text-primary" />
            <span>Path: {location.pathname}</span>
            <span className="text-primary/30">|</span>
            <span>Status: 404_NOT_FOUND</span>
          </motion.div>
        </div>
      </div>

      {/* Bottom Gradient Overlay */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent" />
    </div>
  );
};

export default NotFound;