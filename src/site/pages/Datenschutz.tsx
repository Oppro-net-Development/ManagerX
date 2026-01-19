import { memo } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Shield, Mail } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

const sections = [
  {
    title: "1. Verantwortliche Stelle",
    content: (
      <div className="space-y-2">
        <p>Lenny Steiger</p>
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
        <p>ManagerX verarbeitet personenbezogene Daten nur soweit nötig für die Funktionsfähigkeit des Bots. Dazu gehören insbesondere:</p>
        <ul className="list-disc list-inside space-y-1 text-muted-foreground">
          <li>Discord-ID von Nutzern (zur Identifikation innerhalb von Servern)</li>
          <li>Server-ID (Guild-ID), um Einstellungen pro Server zu speichern</li>
          <li>Einstellungen wie Willkommensnachrichten, Rollen oder Statistiken</li>
          <li>Warnungen / Moderationsaktionen, falls Moderation genutzt wird</li>
          <li>Temporäre Channels / Voice Channels, falls genutzt</li>
          <li>Logdaten (z. B. Timestamps von Aktionen zum Debuggen)</li>
        </ul>
      </div>
    ),
  },
  {
    title: "3. Zweck der Datenverarbeitung",
    content: "Die Daten werden ausschließlich verwendet, um Funktionen des Bots bereitzustellen, Statistiken zu führen, Moderationsaktionen nachzuvollziehen und Fehlerdiagnosen zu ermöglichen. Eine Weitergabe an Dritte erfolgt nicht.",
  },
  {
    title: "4. Rechtsgrundlage",
    content: (
      <div className="space-y-3">
        <p>Die Verarbeitung erfolgt gemäß DSGVO:</p>
        <ul className="list-disc list-inside space-y-1 text-muted-foreground">
          <li>Art. 6 Abs. 1 lit. f DSGVO – berechtigtes Interesse am Bot-Betrieb.</li>
          <li>Art. 6 Abs. 1 lit. b DSGVO – Erfüllung spezifischer Funktionen.</li>
          <li>Art. 6 Abs. 1 lit. a DSGVO – bei Vorliegen einer Einwilligung.</li>
        </ul>
      </div>
    ),
  },
  {
    title: "5. Speicherdauer",
    content: "Daten werden so lange gespeichert, wie sie für die Funktion des Servers notwendig sind oder gesetzliche Aufbewahrungsfristen bestehen. Allgemeine Einstellungen bleiben gespeichert, solange der Bot auf dem Server aktiv ist.",
  },
  {
    title: "6. Rechte der Nutzer",
    content: "Du hast das Recht auf Auskunft, Berichtigung, Löschung und Widerspruch bezüglich deiner Daten. Kontaktiere uns hierzu bitte unter der unten angegebenen E-Mail.",
  },
  {
    title: "7. Datensicherheit",
    content: "ManagerX speichert Daten in SQLite-Datenbanken, die lokal auf dem Server liegen. Es werden angemessene technische Maßnahmen ergriffen, um deine Daten vor unbefugtem Zugriff zu schützen.",
  },
  {
    title: "8. Änderungen",
    content: "Diese Erklärung kann bei neuen Funktionen angepasst werden. Nutzer werden über Discord oder Bot-Kommunikation über Änderungen informiert.",
  },
];

const Datenschutz = memo(function Datenschutz() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container px-4 py-24">
        <Link 
          to="/" 
          className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors mb-8"
        >
          <ArrowLeft className="w-4 h-4" />
          Zurück zur Startseite
        </Link>

        <div className="max-w-3xl mx-auto">
          <div className="flex items-center gap-4 mb-2">
            <Shield className="w-10 h-10 text-primary" />
            <h1 className="text-4xl font-bold">
              <span className="text-gradient">Datenschutzerklärung</span>
            </h1>
          </div>
          <p className="text-muted-foreground mb-12">Gültig für den Discord-Bot ManagerX</p>

          <div className="space-y-6">
            {sections.map((section, index) => (
              <div key={index} className="glass rounded-2xl p-6">
                <h2 className="text-xl font-semibold mb-4 text-foreground">{section.title}</h2>
                <div className="text-muted-foreground leading-relaxed">
                  {section.content}
                </div>
              </div>
            ))}

            <div className="glass rounded-2xl p-6 border border-primary/20">
              <h2 className="text-xl font-semibold mb-4 text-foreground">Datenschutz-Anfrage</h2>
              <p className="text-muted-foreground mb-4">
                Hast du Fragen zu deinen gespeicherten Daten oder möchtest eine Löschung beantragen?
              </p>
              <a 
                href="mailto:contact@oppro-network.de" 
                className="inline-flex items-center gap-2 text-primary hover:underline"
              >
                <Mail className="w-4 h-4" />
                contact@oppro-network.de
              </a>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
});

export default Datenschutz;
