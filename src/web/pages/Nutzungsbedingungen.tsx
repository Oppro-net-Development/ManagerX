import { memo } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, FileText, Mail, Github, Shield } from "lucide-react";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";

const legalSections = [
  {
    title: "1. Geltungsbereich",
    content: "Diese Nutzungsbedingungen regeln die Verwendung des Discord-Bots ManagerX. Mit der Nutzung des Bots oder des bereitgestellten Quellcodes erklärst du dich mit diesen Bedingungen einverstanden.",
  },
  {
    title: "2. Nutzung des Bots",
    content: "ManagerX darf auf Discord-Servern genutzt werden, sofern die erforderlichen Administrations-Rechte vorliegen. Die Nutzung muss den Discord-Richtlinien entsprechen. Missbrauch für Spam oder Belästigung führt zum Ausschluss von der Nutzung.",
  },
  {
    title: "3. Funktionsumfang",
    content: "Der Funktionsumfang von ManagerX umfasst Tools zur Moderation, Community-Verwaltung und Statistiken. Der Betreiber behält sich vor, Funktionen anzupassen oder zu optimieren, um die Stabilität des Systems zu gewährleisten.",
  },
  {
    title: "4. Haftungsausschluss",
    content: "ManagerX Development übernimmt keine Haftung für Schäden oder Datenverluste, die durch die Nutzung des Bots oder fehlerhafte Konfigurationen entstehen könnten.",
  },
  {
    title: "5. Open Source",
    content: "Der Quellcode von ManagerX ist öffentlich zugänglich. Die Nutzung, Modifikation und Weiterverbreitung ist im Rahmen der Lizenzbestimmungen gestattet.",
  },
  {
    title: "6. Änderungen der Bedingungen",
    content: "Diese Bedingungen können bei Bedarf angepasst werden. Die aktuelle Fassung ist jederzeit auf dieser Webseite einsehbar.",
  },
];

export const Nutzungsbedingungen = memo(function Nutzungsbedingungen() {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar />
      
      <main className="flex-grow container relative z-10 px-4 pt-32 pb-24">
        <div className="max-w-3xl mx-auto">
          {/* Zurück Button mit dezentem Hover */}
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

          <header className="mb-16">
            <div className="flex items-center gap-5 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20">
                <Shield className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="text-4xl font-black tracking-tight text-foreground uppercase">
                  Nutzungs<span className="text-primary">bedingungen</span>
                </h1>
                <div className="flex gap-3 mt-1 opacity-40">
                  <span className="text-[10px] font-mono uppercase tracking-widest">Global v2.0.0</span>
                  <span className="text-[10px] font-mono uppercase tracking-widest">•</span>
                  <span className="text-[10px] font-mono uppercase tracking-widest">GPL-3.0</span>
                </div>
              </div>
            </div>
          </header>

          <div className="grid gap-6">
            {legalSections.map((section, index) => (
              <motion.div 
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.05 }}
                className="glass rounded-2xl p-8 border border-white/5 hover:border-primary/10 transition-colors"
              >
                <h2 className="text-lg font-bold mb-4 flex items-center gap-3">
                  <span className="text-primary/30 font-mono text-sm">0{index + 1}</span>
                  {section.title}
                </h2>
                <p className="text-muted-foreground leading-relaxed text-sm md:text-base">
                  {section.content}
                </p>
              </motion.div>
            ))}

            {/* Kontakt Bereich - dezent gehalten */}
            <motion.div 
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              className="mt-12 p-8 rounded-3xl border border-white/5 bg-white/[0.02] flex flex-col md:flex-row items-center justify-between gap-6"
            >
              <div className="text-center md:text-left">
                <h3 className="font-bold">Noch Fragen?</h3>
                <p className="text-sm text-muted-foreground">Kontaktiere das Development-Team.</p>
              </div>
              <div className="flex gap-4">
                <a 
                  href="mailto:development@oppro-network.de" 
                  className="p-3 rounded-xl glass border border-white/10 hover:text-primary transition-colors"
                  title="E-Mail Support"
                >
                  <Mail className="w-5 h-5" />
                </a>
                <a 
                  href="https://github.com/ManagerX-Development/ManagerX" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="p-3 rounded-xl glass border border-white/10 hover:text-primary transition-colors"
                  title="GitHub Repository"
                >
                  <Github className="w-5 h-5" />
                </a>
              </div>
            </motion.div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
});

export default Nutzungsbedingungen;