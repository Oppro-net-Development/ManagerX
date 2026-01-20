import { memo } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Mail, MapPin, User, ShieldCheck } from "lucide-react";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";

export const Impressum = memo(function Impressum() {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar />
      
      <main className="flex-grow container relative z-10 px-4 pt-32 pb-24">
        <div className="max-w-3xl mx-auto">
          {/* Back Button */}
          <motion.div 
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <Link 
              to="/" 
              className="inline-flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors mb-12 group text-sm font-medium"
            >
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
              Zurück zur Startseite
            </Link>
          </motion.div>

          <header className="mb-12">
            <div className="flex items-center gap-5 mb-4">
              <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20">
                <ShieldCheck className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="text-4xl font-black tracking-tight text-foreground uppercase">
                  Impres<span className="text-primary">sum</span>
                </h1>
                <p className="text-muted-foreground font-mono text-[10px] uppercase tracking-widest mt-1 opacity-50">
                  Angaben gemäß § 5 TMG
                </p>
              </div>
            </div>
          </header>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass rounded-3xl p-8 md:p-12 border border-white/5 space-y-12"
          >
            {/* Verantwortlich */}
            <section className="flex flex-col md:flex-row md:items-start gap-6">
              <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center shrink-0 border border-white/10">
                <User className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h2 className="text-sm font-bold uppercase tracking-widest text-primary mb-3">Verantwortlich</h2>
                <p className="text-xl font-semibold text-foreground">Lenny Steiger</p>
              </div>
            </section>

            {/* Anschrift */}
            <section className="flex flex-col md:flex-row md:items-start gap-6">
              <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center shrink-0 border border-white/10">
                <MapPin className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h2 className="text-sm font-bold uppercase tracking-widest text-primary mb-3">Anschrift</h2>
                <div className="space-y-1 text-muted-foreground leading-relaxed">
                  <p>Eulauer Str. 24</p>
                  <p>04523 Pegau</p>
                  <p>Deutschland</p>
                </div>
              </div>
            </section>

            {/* Kontakt */}
            <section className="flex flex-col md:flex-row md:items-start gap-6">
              <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center shrink-0 border border-white/10">
                <Mail className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h2 className="text-sm font-bold uppercase tracking-widest text-primary mb-3">Kontakt</h2>
                <a 
                  href="mailto:contact@oppro-network.de" 
                  className="text-lg font-medium text-foreground hover:text-primary transition-colors underline decoration-primary/30 underline-offset-4"
                >
                  contact@oppro-network.de
                </a>
              </div>
            </section>
          </motion.div>

          {/* Optional Footer Disclaimer */}
          <p className="mt-8 text-center text-[11px] text-muted-foreground/40 leading-relaxed max-w-xl mx-auto italic">
            Dieses Impressum gilt auch für unsere Social-Media-Präsenzen und den Discord-Bot ManagerX.
          </p>
        </div>
      </main>

      <Footer />
    </div>
  );
});

export default Impressum;