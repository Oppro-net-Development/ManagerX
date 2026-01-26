import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { 
  Shield, Menu, X, Sparkles, Puzzle, Activity, 
  Newspaper // Icon für den Blog hinzugefügt
} from "lucide-react"; 
import { cn } from "@/lib/utils";

const navLinks = [
  { label: "Features", href: "/#features", icon: Sparkles },
  { label: "Plugins", href: "/plugins", icon: Puzzle },
  { label: "Status", href: "/status", icon: Activity },
];

export function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.8, ease: "easeInOut" }}
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-700 ease-out",
        isScrolled ? "glass-strong py-3 shadow-lg shadow-primary/5" : "py-5 bg-transparent"
      )}
    >
      <div className="container px-4">
        <nav className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <motion.div 
              className="w-11 h-11 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center glow-subtle shadow-lg shadow-primary/20 text-white"
              whileHover={{ rotate: 10, scale: 1.1 }}
            >
              <Shield className="w-5 h-5" />
            </motion.div>
            <span className="text-xl font-bold tracking-tighter text-white">
              Manager<span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">X</span>
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-2">
            {navLinks.map((link, idx) => (
              <motion.div key={link.label} initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.1 }}>
                <Link
                  to={link.href}
                  className={cn(
                    "relative text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-300 group flex items-center gap-2 px-4 py-2 rounded-lg",
                    location.pathname === link.href 
                      ? "text-primary bg-primary/10" 
                      : "text-muted-foreground hover:text-white hover:bg-white/5"
                  )}
                >
                  {link.icon && <link.icon className="w-4 h-4" />}
                  {link.label}
                  <span className={cn(
                    "absolute -bottom-1 left-0 h-0.5 bg-gradient-to-r from-primary to-accent transition-all duration-300 rounded-full",
                    location.pathname === link.href ? "w-[calc(100%-32px)] ml-4" : "w-0 group-hover:w-[calc(100%-32px)]"
                  )} />
                </Link>
              </motion.div>
            ))}
          </div>

          {/* CTA Button */}
          <div className="hidden md:block">
            <motion.a
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.98 }}
              href="https://discord.com/oauth2/authorize?client_id=1368201272624287754&permissions=1669118160151&integration_type=0&scope=bot" 
              target="_blank" 
              rel="noopener noreferrer"
              className="group inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-primary to-accent text-white font-bold hover:shadow-lg hover:shadow-primary/50 transition-all"
            >
              <Sparkles className="w-4 h-4 group-hover:rotate-12 transition-transform" />
              Bot einladen
            </motion.a>
          </div>

          {/* Mobile Menu Button */}
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 text-white hover:bg-white/5 rounded-lg transition-colors"
          >
            {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </motion.button>
        </nav>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="md:hidden glass border-b border-white/10 backdrop-blur-lg"
          >
            <div className="container py-10 flex flex-col gap-6">
              {navLinks.map((link, idx) => (
                <motion.div 
                  key={link.label}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                >
                  <Link 
                    to={link.href} 
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={cn(
                      "text-lg font-bold uppercase flex items-center gap-3 p-3 rounded-lg transition-colors",
                      location.pathname === link.href 
                        ? "text-primary bg-primary/10" 
                        : "text-foreground/80 hover:text-white hover:bg-white/5"
                    )}
                  >
                    {link.icon && <link.icon className="w-5 h-5 text-primary" />}
                    {link.label}
                  </Link>
                </motion.div>
              ))}
              <motion.a 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                href="https://discord.com/oauth2/authorize?client_id=1368201272624287754&permissions=1669118160151&integration_type=0&scope=bot" 
                target="_blank"
                rel="noopener noreferrer"
                className="mt-6 inline-flex items-center justify-center gap-2 bg-gradient-to-r from-primary to-accent text-white p-4 rounded-2xl text-center font-bold uppercase tracking-widest hover:shadow-lg transition-all"
              >
                <Sparkles className="w-4 h-4" />
                Bot einladen
              </motion.a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}