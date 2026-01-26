import { memo } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Mail, MapPin, User, ShieldCheck } from "lucide-react";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";
import { motion } from "framer-motion";

export const Impressum = memo(function Impressum() {
  return (
    <div 
      className="min-h-screen bg-background flex flex-col"
    >
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
                <h2 className="text-sm font-bold uppercase tracking-widest text-primary mb-3">Verantwortliche Person (§5 TMG)</h2>
                <p className="text-xl font-semibold text-foreground">Lenny Steiger</p>
                <p className="text-sm text-muted-foreground mt-1">Gründer & Projektleiter</p>
              </div>
            </section>

            {/* Anschrift */}
            <section className="flex flex-col md:flex-row md:items-start gap-6">
              <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center shrink-0 border border-white/10">
                <MapPin className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h2 className="text-sm font-bold uppercase tracking-widest text-primary mb-3">Adresse</h2>
                <div className="space-y-1 text-muted-foreground leading-relaxed text-sm">
                  <p>Lenny Steiger</p>
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
                <div className="space-y-2">
                  <div>
                    <p className="text-xs text-muted-foreground/70">E-Mail (Allgemein):</p>
                    <a 
                      href="mailto:contact@oppro-network.de" 
                      className="text-sm font-medium text-foreground hover:text-primary transition-colors"
                    >
                      contact@oppro-network.de
                    </a>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground/70">E-Mail (Legal):</p>
                    <a 
                      href="mailto:legal@oppro-network.de" 
                      className="text-sm font-medium text-foreground hover:text-primary transition-colors"
                    >
                      legal@oppro-network.de
                    </a>
                  </div>
                </div>
              </div>
            </section>

            {/* Rechtliche Hinweise */}
            <section className="border-t border-white/5 pt-8 space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-widest text-primary mb-4">Rechtliche Informationen</h2>
              
              <div className="space-y-3 text-sm text-muted-foreground">
                <div>
                  <p className="font-medium text-foreground mb-1">Haftungsausschluss (§ 7 TMG)</p>
                  <p>Als Diensteanbieter sind wir gemäß § 7 Abs.1 TMG für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 TMG sind wir als Diensteanbieter jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen.</p>
                </div>

                <div>
                  <p className="font-medium text-foreground mb-1">Haftung für Links</p>
                  <p>Unsere Website enthält Links zu externen Websites. Für die Inhalte der verlinkten Seiten sind wir nicht verantwortlich. Die Betreiber der verlinkten Seiten sind allein für deren Inhalte verantwortlich.</p>
                </div>

                <div>
                  <p className="font-medium text-foreground mb-1">Urheberrecht</p>
                  <p>Die Inhalte und Werke auf dieser Website sind urheberrechtlich geschützt. Eine Vervielfältigung, Bearbeitung, Verbreitung oder jede Art der Verwertung außerhalb der Grenzen des Urheberrechts bedarf der vorherigen schriftlichen Zustimmung des Autors oder Erstellers. Der Quellcode ist unter der <strong>GPL-3.0 Lizenz</strong> verfügbar.</p>
                </div>

                <div>
                  <p className="font-medium text-foreground mb-1">Hosting & GitHub Pages</p>
                  <p>Diese Website wird gehostet auf <strong>GitHub Pages</strong> (GitHub Inc., San Francisco, USA). Informationen zur Datenverarbeitung finden Sie unter: <a href="https://docs.github.com/en/github/site-policy/github-privacy-statement" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">GitHub Privacy Statement</a></p>
                </div>

                <div>
                  <p className="font-medium text-foreground mb-1">Datenschutz</p>
                  <p>Siehe unsere <Link to="/datenschutz" className="text-primary hover:underline">Datenschutzerklärung</Link> für Informationen über die Verarbeitung personenbezogener Daten.</p>
                </div>

                <div>
                  <p className="font-medium text-foreground mb-1">Nutzungsbedingungen</p>
                  <p>Die <Link to="/nutzungsbedingungen" className="text-primary hover:underline">Nutzungsbedingungen</Link> regeln die Verwendung dieses Services.</p>
                </div>
              </div>
            </section>

            {/* Streitbeilegung */}
            <section className="border-t border-white/5 pt-8 space-y-3">
              <h2 className="text-sm font-bold uppercase tracking-widest text-primary mb-4">Streitbeilegung</h2>
              <p className="text-sm text-muted-foreground">
                Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: <a href="https://ec.europa.eu/consumers/odr/" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">https://ec.europa.eu/consumers/odr/</a>
              </p>
              <p className="text-xs text-muted-foreground/70">Wir sind nicht bereit und nicht verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>
            </section>

            {/* Letzte Aktualisierung */}
            <section className="border-t border-white/5 pt-8">
              <p className="text-xs text-muted-foreground/60">Letzte Aktualisierung: Januar 2026</p>
            </section>
          </motion.div>

          {/* Optional Footer Disclaimer */}
          <p className="mt-8 text-center text-[10px] text-muted-foreground/40 leading-relaxed max-w-xl mx-auto">
            Dieses Impressum gilt auch für unsere Social-Media-Präsenzen und den Discord-Bot ManagerX. Das Projekt wird entwickelt und gehostet von OPPRO.NET Network.
          </p>
        </div>
      </main>

      <Footer />
    </div>
  );
});

export default Impressum;