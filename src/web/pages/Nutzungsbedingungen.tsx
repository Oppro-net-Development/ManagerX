import { memo } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, FileText, Mail, Github, Shield } from "lucide-react";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";

const legalSections = [
  {
    title: "1. Geltungsbereich",
    content: "Diese Nutzungsbedingungen regeln die Verwendung des Discord-Bots ManagerX sowie dieser Website. Mit der Nutzung des Bots, der Website oder des Quellcodes erklärst du dich mit diesen Bedingungen einverstanden.",
  },
  {
    title: "2. Lizenz & Open Source",
    content: (
      <div className="space-y-2 text-sm">
        <p>ManagerX wird unter der <strong>GNU General Public License v3.0 (GPL-3.0)</strong> lizenziert.</p>
        <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
          <li>Quellcode darf frei eingesehen, modifiziert und verbreitet werden</li>
          <li>Modifikationen müssen ebenfalls unter GPL-3.0 lizenziert werden</li>
          <li>Kommerzielles Hosting ist gestattet, Quellcode muss verfügbar sein</li>
        </ul>
      </div>
    ),
  },
  {
    title: "3. Bot-Nutzung",
    content: (
      <div className="space-y-2 text-sm">
        <p>ManagerX darf auf Discord-Servern genutzt werden, sofern:</p>
        <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
          <li>Sie Admin-Rechte auf dem Server haben</li>
          <li>Die Nutzung den Discord Terms of Service entspricht</li>
          <li>Sie keine illegalen oder schädlichen Aktivitäten durchführen</li>
          <li>Sie keine Spam-, Phishing- oder Hacking-Funktionen implementieren</li>
        </ul>
      </div>
    ),
  },
  {
    title: "4. Verbotene Nutzung",
    content: (
      <div className="space-y-2 text-sm">
        <p>Folgende Aktivitäten sind streng untersagt:</p>
        <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
          <li>Reverse Engineering zu böswilligen Zwecken</li>
          <li>DDoS-Attacken oder Sicherheitsverstöße</li>
          <li>Automatisierte Spam- oder Harassment-Kampagnen</li>
          <li>Verbreitung von Malware oder Exploits</li>
          <li>Verstöße gegen Discord Community Guidelines</li>
        </ul>
        <p className="mt-2"><strong>Konsequenz:</strong> Sofortiger Ausschluss und mögliche Benachrichtigung von Discord & Strafverfolgungsbehörden</p>
      </div>
    ),
  },
  {
    title: "5. Haftungsausschluss",
    content: (
      <div className="space-y-2 text-sm">
        <p>OPPRO.NET Network und die Betreiber von ManagerX übernehmen <strong>keine Haftung</strong> für:</p>
        <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
          <li>Datenverluste durch Bot-Fehler oder Misconfiguration</li>
          <li>Ausfallzeiten oder Performance-Probleme</li>
          <li>Direkte, indirekte oder Folgeschäden</li>
          <li>Discord API-Änderungen, die Funktionen beeinflussen</li>
          <li>Verlust von Server-Daten durch User-Fehler</li>
        </ul>
        <p className="mt-2 italic">Der Bot wird "AS IS" (ohne Gewährleistung) bereitgestellt.</p>
      </div>
    ),
  },
  {
    title: "6. Funktionalität & Änderungen",
    content: (
      <div className="space-y-2 text-sm">
        <p>Wir behalten uns das Recht vor:</p>
        <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
          <li>Funktionen zu aktualisieren, zu optimieren oder zu entfernen</li>
          <li>Wartungsarbeiten ohne vorherige Ankündigung durchzuführen</li>
          <li>Den Bot zeitweise offline zu nehmen</li>
          <li>Nutzungsrichtlinien zu ändern (mit 30 Tagen Ankündigung)</li>
        </ul>
      </div>
    ),
  },
  {
    title: "7. Datenschutz & Datenverwaltung",
    content: (
      <div className="space-y-2 text-sm">
        <p>Siehe unsere <Link to="/datenschutz" className="text-primary hover:underline">Datenschutzerklärung</Link> für Details über:</p>
        <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
          <li>Erhobene und verarbeitete Daten</li>
          <li>Dauer der Speicherung</li>
          <li>Ihre Rechte nach DSGVO</li>
          <li>Kontaktinformationen für Datenschutzanfragen</li>
        </ul>
      </div>
    ),
  },
  {
    title: "8. Geistiges Eigentum",
    content: (
      <div className="space-y-2 text-sm">
        <p>ManagerX und die Website-Inhalte (außer Open-Source Code) sind urheberrechtlich geschützt.</p>
        <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
          <li>Logos, Design und UI sind Eigentum von OPPRO.NET</li>
          <li>Source Code ist unter GPL-3.0 lizenziert und frei verwendbar</li>
          <li>Dokumentation ist unter der Lizenz des Projekts verfügbar</li>
        </ul>
      </div>
    ),
  },
  {
    title: "9. Benutzercommunity & Support",
    content: (
      <div className="space-y-2 text-sm">
        <p>Support wird bereitgestellt über:</p>
        <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
          <li>GitHub Issues für Bug Reports und Feature Requests</li>
          <li>E-Mail: support@oppro-network.de</li>
          <li>Discord Server (falls vorhanden)</li>
        </ul>
        <p className="mt-2"><strong>Hinweis:</strong> Support ist gemeinschaftlich und kann nicht garantiert werden.</p>
      </div>
    ),
  },
  {
    title: "10. Beendigung der Nutzung",
    content: (
      <div className="space-y-2 text-sm">
        <p>Wir können Ihren Zugriff beenden, wenn Sie:</p>
        <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
          <li>Gegen diese Bedingungen verstoßen</li>
          <li>Den Bot zu schädlichen Zwecken nutzen</li>
          <li>Unsere Ressourcen missbrauchen</li>
        </ul>
      </div>
    ),
  },
  {
    title: "11. Abhängigkeiten & Third-Party",
    content: (
      <div className="space-y-2 text-sm">
        <p>ManagerX nutzt External Libraries und Services:</p>
        <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
          <li>discord.py / py-cord: Offizielle Discord API Library</li>
          <li>FastAPI & Uvicorn: Python Web Framework</li>
          <li>SQLite: Datenbankengine</li>
          <li>Dritte Dienste gemäß requirements.txt</li>
        </ul>
        <p className="mt-2">Siehe <code className="bg-white/5 px-2 py-1 rounded text-xs">requirements/req.txt</code> für vollständige Liste.</p>
      </div>
    ),
  },
  {
    title: "12. Änderungen dieser Bedingungen",
    content: (
      <div className="space-y-2 text-sm">
        <p>Diese Bedingungen können jederzeit geändert werden. Bedeutende Änderungen werden mit 30 Tagen Ankündigung kommuniziert.</p>
        <p className="text-xs text-muted-foreground/60">Letzte Aktualisierung: Januar 2026</p>
      </div>
    ),
  },
  {
    title: "13. Geltend geltendes Recht",
    content: "Diese Bedingungen unterliegen deutschem Recht. Gerichtsstand ist Deutschland.",
  },
  {
    title: "14. Kontakt bei Fragen",
    content: (
      <div className="space-y-2 text-sm">
        <p>
          Rechtliche oder vertragliche Fragen:{" "}
          <a href="mailto:legal@oppro-network.de" className="text-primary hover:underline">
            legal@oppro-network.de
          </a>
        </p>
        <p>
          Support & Allgemeine Anfragen:{" "}
          <a href="mailto:support@oppro-network.de" className="text-primary hover:underline">
            support@oppro-network.de
          </a>
        </p>
      </div>
    ),
  },
];

export const Nutzungsbedingungen = memo(function Nutzungsbedingungen() {
  return (
    <div 
      className="min-h-screen bg-background flex flex-col"
    >
      <Navbar />
      
      <main className="flex-grow container relative z-10 px-4 pt-32 pb-24">
        <div className="max-w-3xl mx-auto">
          {/* Zurück Button mit dezentem Hover */}
          <div 
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
          </div>

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