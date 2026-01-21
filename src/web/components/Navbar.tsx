import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Shield, Menu, X, Sparkles, Puzzle, Activity } from "lucide-react"; // Activity Icon hinzugefügt
import { cn } from "@/lib/utils";

const navLinks = [
  { label: "Features", href: "/#features" },
  { label: "Plugins", href: "/plugins", icon: Puzzle },
  { label: "Status", href: "/status", icon: Activity }, // Status Link hinzugefügt
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
      transition={{ duration: 0.6, ease: "easeOut" }}
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-500",
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
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.label}
                to={link.href}
                className={cn(
                  "relative text-[10px] font-black uppercase tracking-[0.2em] transition-colors group flex items-center gap-2",
                  location.pathname === link.href ? "text-primary" : "text-muted-foreground hover:text-white"
                )}
              >
                {link.icon && <link.icon className="w-3.5 h-3.5" />}
                {link.label}
                <span className={cn(
                  "absolute -bottom-1 left-0 h-0.5 bg-gradient-to-r from-primary to-accent transition-all duration-300",
                  location.pathname === link.href ? "w-full" : "w-0 group-hover:w-full"
                )} />
              </Link>
            ))}
          </div>

          {/* CTA Button */}
          <div className="hidden md:block">
            <Button variant="default" className="group bg-primary hover:bg-primary/90 rounded-xl px-6 text-white font-bold" asChild>
              <a href="https://discord.com" target="_blank" rel="noopener noreferrer">
                <Sparkles className="w-4 h-4 mr-2 group-hover:rotate-12 transition-transform" />
                Bot einladen
              </a>
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 text-white"
          >
            {isMobileMenuOpen ? <X /> : <Menu />}
          </button>
        </nav>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-background/95 backdrop-blur-lg border-b border-white/5"
          >
            <div className="container py-8 flex flex-col gap-6">
              {navLinks.map((link) => (
                <Link 
                  key={link.label}
                  to={link.href} 
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={cn(
                    "text-2xl font-black italic uppercase flex items-center gap-3",
                    location.pathname === link.href ? "text-primary" : "text-white"
                  )}
                >
                  {link.icon && <link.icon className="w-6 h-6 text-primary" />}
                  {link.label}
                </Link>
              ))}
              <a 
                href="https://discord.com" 
                className="mt-4 bg-primary text-white p-4 rounded-2xl text-center font-black uppercase italic tracking-widest"
              >
                Bot einladen
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}