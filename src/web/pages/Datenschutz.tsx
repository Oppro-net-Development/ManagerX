import { memo } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Shield, Mail, Lock, Database } from "lucide-react";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";

export const Datenschutz = memo(function Datenschutz() {
  const sections = [
    {
      title: "1. Verantwortliche Stelle",
      content: (
        <div className="space-y-2">
          <p className="font-medium text-foreground">Lenny Steiger</p>
          <p>
            E-Mail:{" "}
            <a href="mailto:contact@oppro-network.de" className="text-primary hover:underline">
              contact@oppro-network.de
            </a>
          </p>
          <p>Verantwortlich für die Datenverarbeitung im Rahmen der Nutzung von ManagerX.</p>
        </div>
      ),
    },
    {
      title: "2. Erhobene Daten",
      content: (
        <div className="space-y-3">
          <p>ManagerX verarbeitet personenbezogene Daten nur soweit nötig. Dazu gehören:</p>
          <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
            <li>Discord-ID & Server-ID (zur Identifikation)</li>
            <li>Server-Einstellungen (Willkommen, Rollen, Statistiken)</li>
            <li>Moderationsdaten (Warnungen, Kicks, Bans)</li>
            <li>Temporäre Voice-Channel Daten</li>
            <li>Logdaten zur Fehlerdiagnose (Timestamps)</li>
          </ul>
        </div>
      ),
    },
    {
      title: "3. Zweck der Verarbeitung",
      content: "Die Daten dienen ausschließlich der Bereitstellung der Bot-Funktionen, der Nachvollziehbarkeit von Moderationsaktionen und der Fehlerdiagnose. Eine Weitergabe an Dritte erfolgt nicht.",
    },
    {
      title: "4. Rechtsgrundlage",
      content: (
        <div className="space-y-2 italic text-sm">
          <p>Art. 6 Abs. 1 lit. f DSGVO – berechtigtes Interesse am Bot-Betrieb.</p>
          <p>Art. 6 Abs. 1 lit. b DSGVO – Erfüllung spezifischer Funktionen.</p>
        </div>
      ),
    },
    {
      title: "5. Speicherdauer & Sicherheit",
      content: "Daten werden gespeichert, solange der Bot auf dem Server aktiv ist oder gesetzliche Fristen dies erfordern. Die Speicherung erfolgt in SQLite-Datenbanken mit angemessenen technischen Schutzmaßnahmen.",
    },
    {
      title: "6. Rechte der Nutzer",
      content: "Du hast jederzeit das Recht auf Auskunft, Berichtigung oder Löschung deiner Daten. Anfragen können direkt per E-Mail an uns gestellt werden.",
    },
  ];

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar />
      
      <main className="flex-grow container relative z-10 px-4 pt-32 pb-24">
        <div className="max-w-3xl mx-auto">
          {/* Back Link */}
          <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}>
            <Link 
              to="/" 
              className="inline-flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors mb-12 group text-sm font-medium"
            >
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
              Zurück zur Startseite
            </Link>
          </motion.div>

          <header className="mb-16">
            <div className="flex items-center gap-5 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20">
                <Lock className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="text-4xl font-black tracking-tight text-foreground uppercase leading-none">
                  Daten<span className="text-primary">schutz</span>
                </h1>
                <div className="flex gap-3 mt-2 opacity-40">
                  <span className="text-[10px] font-mono uppercase tracking-widest">DSGVO Konform</span>
                  <span className="text-[10px] font-mono uppercase tracking-widest">•</span>
                  <span className="text-[10px] font-mono uppercase tracking-widest">SQLite Secure</span>
                </div>
              </div>
            </div>
          </header>

          <div className="grid gap-6">
            {sections.map((section, index) => (
              <motion.div 
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.05 }}
                className="glass rounded-2xl p-8 border border-white/5 hover:border-primary/10 transition-colors"
              >
                <h2 className="text-lg font-bold mb-4 flex items-center gap-3">
                  <Database className="w-4 h-4 text-primary/40" />
                  {section.title}
                </h2>
                <div className="text-muted-foreground leading-relaxed text-sm md:text-base">
                  {section.content}
                </div>
              </motion.div>
            ))}

            {/* Kontakt Footer */}
            <motion.div 
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              className="mt-12 p-8 rounded-3xl border border-primary/10 bg-primary/[0.02] flex flex-col items-center text-center gap-4"
            >
              <div className="w-12 h-12 rounded-full bg-background flex items-center justify-center border border-primary/20 mb-2">
                <Shield className="w-6 h-6 text-primary" />
              </div>
              <h3 className="font-bold text-xl">Datenschutz-Anfrage</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                Möchtest du eine Auskunft über deine Daten oder eine vollständige Löschung beantragen?
              </p>
              <a 
                href="mailto:contact@oppro-network.de" 
                className="inline-flex items-center gap-2 mt-2 px-6 py-2 bg-primary text-primary-foreground rounded-xl font-bold text-sm hover:opacity-90 transition-opacity"
              >
                <Mail className="w-4 h-4" />
                Anfrage senden
              </a>
            </motion.div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
});

export default Datenschutz;