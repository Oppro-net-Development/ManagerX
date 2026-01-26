import { memo } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Shield, Mail, Lock, Database } from "lucide-react";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";

export const Datenschutz = memo(function Datenschutz() {
  const sections = [
    {
      title: "1. Verantwortliche Stelle",
      content: (
        <div className="space-y-2">
          <p className="font-medium text-foreground">OPPRO.NET Network</p>
          <p>Verantwortlicher im Sinne der DSGVO:</p>
          <p className="text-sm">
            Lenny Steiger<br />
            E-Mail:{" "}
            <a href="mailto:contact@oppro-network.de" className="text-primary hover:underline">
              contact@oppro-network.de
            </a>
          </p>
        </div>
      ),
    },
    {
      title: "2. Datenschutzbeauftragter",
      content: (
        <div className="space-y-2">
          <p>Bei Datenschutzfragen können Sie sich an:</p>
          <p className="text-sm">
            E-Mail:{" "}
            <a href="mailto:datenschutz@oppro-network.de" className="text-primary hover:underline">
              datenschutz@oppro-network.de
            </a>
          </p>
        </div>
      ),
    },
    {
      title: "3. Erhobene Personenbezogene Daten",
      content: (
        <div className="space-y-3">
          <p>Bei der Nutzung von ManagerX verarbeiten wir folgende Daten:</p>
          <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2 text-sm">
            <li><strong>Discord-IDs:</strong> Nutzer-ID, Server-ID zur eindeutigen Identifikation</li>
            <li><strong>Benutzername & Avatar:</strong> Für Logging und Audit-Trail</li>
            <li><strong>Server-Konfigurationen:</strong> Einstellungen wie Willkommenskanäle, Automoderation, Rollen</li>
            <li><strong>Moderationsdaten:</strong> Verwarnungen, Kicks, Bans mit Gründen und Zeitstempel</li>
            <li><strong>XP/Level-Daten:</strong> Aktivitätsstatistiken zur Gamification</li>
            <li><strong>Voice-Channel-Daten:</strong> Temporäre Kanäle und deren Einstellungen</li>
            <li><strong>Log-Daten:</strong> Timestamps und Fehlerdiagnose-Informationen</li>
          </ul>
        </div>
      ),
    },
    {
      title: "4. Zweck der Datenverarbeitung",
      content: (
        <div className="space-y-3">
          <p>Die Daten werden ausschließlich für folgende Zwecke verarbeitet:</p>
          <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2 text-sm">
            <li>Bereitstellung und Verwaltung der Bot-Funktionen</li>
            <li>Nachvollziehbarkeit von Moderationsmaßnahmen (Audit-Trail)</li>
            <li>Fehlerdiagnose und technische Optimierung</li>
            <li>Statistiken und Leistungsanalyse</li>
            <li>Compliance mit Discord-Richtlinien</li>
          </ul>
        </div>
      ),
    },
    {
      title: "5. Rechtsgrundlage der Verarbeitung",
      content: (
        <div className="space-y-2 text-sm">
          <p><strong>Art. 6 Abs. 1 lit. f DSGVO:</strong> Berechtigtes Interesse am Bot-Betrieb und Systemsicherheit</p>
          <p><strong>Art. 6 Abs. 1 lit. b DSGVO:</strong> Erfüllung der Vertragsbestimmungen bei der Nutzung des Bots</p>
          <p><strong>Art. 6 Abs. 1 lit. c DSGVO:</strong> Einhaltung gesetzlicher Verpflichtungen</p>
        </div>
      ),
    },
    {
      title: "6. Speicherdauer",
      content: (
        <div className="space-y-2 text-sm">
          <p><strong>Moderationsdaten:</strong> Speicherung für 2 Jahre ab Eintrag (zur Nachverfolgung von Verstößen)</p>
          <p><strong>Server-Konfigurationen:</strong> Solange der Bot aktiv ist oder bis zur Löschung</p>
          <p><strong>XP/Level-Daten:</strong> Bis zur aktiven Löschung durch Server-Admin oder Bot-Entfernung</p>
          <p><strong>Log-Daten:</strong> Maximale Speicherung von 90 Tagen für technische Fehlerdiagnose</p>
        </div>
      ),
    },
    {
      title: "7. Empfänger der Daten",
      content: (
        <div className="space-y-2 text-sm">
          <p>Eine Weitergabe der Daten erfolgt an folgende Partner:</p>
          <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
            <li><strong>Discord:</strong> Als API-Partner (Hostingpartner für Bot-Daten)</li>
            <li><strong>GitHub Pages:</strong> Hosting der Website (Datenschutzerklärung: https://docs.github.com/en/github/site-policy/github-privacy-statement)</li>
            <li><strong>GitHub Inc.:</strong> Hosting-Provider (Microsoft-Tochter, US-basiert, Standard Contractual Clauses)</li>
          </ul>
          <p className="mt-2">Weitere Datenübertragungen erfolgen nur wenn:</p>
          <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
            <li>Gesetzliche Verpflichtungen eine Herausgabe erfordern</li>
            <li>Strafverfolgungsbehörden eine Anfrage stellen</li>
          </ul>
        </div>
      ),
    },
    {
      title: "8. Datensicherheit",
      content: (
        <div className="space-y-2 text-sm">
          <p>Ihre Daten werden geschützt durch:</p>
          <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
            <li>SQLite-Datenbanken mit Zugriffskontrolle</li>
            <li>Verschlüsselte Verbindungen (Discord API über HTTPS)</li>
            <li>Regelmäßige Backups</li>
            <li>Begrenzte Zugriffe (nur authorisierte Administratoren)</li>
          </ul>
          <p className="mt-2">Vollständige Garantie auf Sicherheit kann nicht gegeben werden, da das Internet nicht vollständig sicher ist.</p>
        </div>
      ),
    },
    {
      title: "9. Ihre Rechte (Art. 15-22 DSGVO)",
      content: (
        <div className="space-y-2 text-sm">
          <p>Sie haben das Recht auf:</p>
          <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
            <li><strong>Auskunft:</strong> Kostenlose Einsicht in Ihre verarbeiteten Daten</li>
            <li><strong>Berichtigung:</strong> Korrektur fehlerhafter Daten</li>
            <li><strong>Löschung (Recht auf Vergessenwerden):</strong> Löschung aller Daten (außer bei Speicherpflichten)</li>
            <li><strong>Datenportabilität:</strong> Übermittlung in gängigem Format</li>
            <li><strong>Widerspruch:</strong> Gegen die Verarbeitung Ihrer Daten</li>
          </ul>
          <p className="mt-2">Anfragen richten Sie bitte an: <a href="mailto:datenschutz@oppro-network.de" className="text-primary hover:underline">datenschutz@oppro-network.de</a></p>
        </div>
      ),
    },
    {
      title: "10. Beschwderecht",
      content: (
        <div className="space-y-2 text-sm">
          <p>Sie haben das Recht, bei einer Datenschutzbehörde Beschwerde einzureichen, wenn Sie der Meinung sind, dass die Verarbeitung gegen die DSGVO verstößt.</p>
          <p>Zuständige Behörde: Landesdatenschutzbehörde (je nach Bundesland)</p>
        </div>
      ),
    },
    {
      title: "11. Automatisierte Entscheidungsfindung",
      content: "ManagerX trifft keine vollautomatisierten Entscheidungen, die erhebliche Auswirkungen haben. Alle Moderationsmaßnahmen basieren auf manuellen Triggers oder Admin-Entscheidungen.",
    },
    {
      title: "12. Cookies & Tracking",
      content: "Die Website nutzt keine Cookies oder Tracking-Technologien. Die React-App speichert nur lokale Session-Daten im Browser.",
    },
    {
      title: "13. GitHub Pages Hosting",
      content: (
        <div className="space-y-2 text-sm">
          <p>Diese Website wird auf <strong>GitHub Pages</strong> gehostet.</p>
          <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
            <li><strong>Hostingpartner:</strong> GitHub Inc. (Microsoft-Tochter), San Francisco, USA</li>
            <li><strong>Rechtliche Grundlage:</strong> Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse)</li>
            <li><strong>Datenschutz:</strong> <a href="https://docs.github.com/en/github/site-policy/github-privacy-statement" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">GitHub Privacy Statement</a></li>
            <li><strong>Datenübertragung in die USA:</strong> Erfolgt unter Standard Contractual Clauses (SCC)</li>
            <li><strong>Protokollierte Daten:</strong> GitHub Pages protokolliert IP-Adressen und Zugriffsdaten für Sicherheit</li>
          </ul>
          <p className="mt-2 italic">Siehe GitHub Privacy Statement für Details zur Datenverarbeitung.</p>
        </div>
      ),
    },
    {
      title: "14. Änderungen dieser Datenschutzerklärung",
      content: "Wir können diese Datenschutzerklärung jederzeit aktualisieren. Änderungen werden auf dieser Seite veröffentlicht. Fortgesetzte Nutzung nach Änderungen bedeutet Zustimmung.",
    },
    {
      title: "15. Kontakt",
      content: (
        <div className="space-y-2 text-sm">
          <p>Für Datenschutzfragen kontaktieren Sie uns unter:</p>
          <p>
            <a href="mailto:datenschutz@oppro-network.de" className="text-primary hover:underline">
              datenschutz@oppro-network.de
            </a>
          </p>
          <p className="text-xs text-muted-foreground/60">Letzte Aktualisierung: Januar 2026</p>
        </div>
      ),
    },
  ];

  return (
    <div 
      className="min-h-screen bg-background flex flex-col"
    >
      <Navbar />
      
      <main className="flex-grow container relative z-10 px-4 pt-32 pb-24">
        <div className="max-w-3xl mx-auto">
          {/* Back Link */}
          <div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}>
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
              <h3 className="font-bold text-xl">Ihre Datenschutzrechte</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                Möchten Sie Ihre Daten einsehen, korrigieren, löschen oder exportieren?
              </p>
              <div className="flex flex-col gap-2 mt-2 w-full">
                <a 
                  href="mailto:datenschutz@oppro-network.de?subject=DSGVO-Anfrage" 
                  className="inline-flex items-center justify-center gap-2 px-6 py-2 bg-primary text-primary-foreground rounded-xl font-bold text-sm hover:opacity-90 transition-opacity"
                >
                  <Mail className="w-4 h-4" />
                  Datenschutz-Anfrage
                </a>
                <p className="text-xs text-muted-foreground/60">Antwortzeit: innerhalb von 30 Tagen nach DSGVO</p>
              </div>
            </motion.div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
});

export default Datenschutz;