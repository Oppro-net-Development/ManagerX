import { memo } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, FileText, Mail } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

const sections = [
  {
    title: "1. Geltungsbereich",
    content: "Diese Nutzungsbedingungen regeln die Verwendung des Discord-Bots ManagerX, betrieben von OPPRO.NET Network. Mit der Nutzung des Bots erklärst du dich mit diesen Bedingungen einverstanden.",
  },
  {
    title: "2. Nutzung des Bots",
    content: (
      <ul className="list-disc list-inside space-y-2 text-muted-foreground">
        <li>ManagerX darf nur in Discord-Servern genutzt werden, auf denen du Administrator oder mit Erlaubnis des Administrators bist.</li>
        <li>Du bist dafür verantwortlich, dass die Nutzung des Bots den Discord-Richtlinien und den geltenden Gesetzen entspricht.</li>
        <li>Der Bot darf nicht für illegale Aktivitäten, Spam, Belästigung oder andere schädliche Zwecke verwendet werden.</li>
      </ul>
    ),
  },
  {
    title: "3. Funktionsumfang",
    content: "ManagerX bietet Funktionen wie Moderation (Warnungen, Kicks, Bans), Welcome-System, Temp Voice Channels, Statistiken und weitere Tools. Der Betreiber von ManagerX behält sich das Recht vor, Funktionen zu ändern, hinzuzufügen oder zu entfernen.",
  },
  {
    title: "4. Haftung",
    content: "ManagerX Development übernimmt keine Haftung für Schäden, die direkt oder indirekt durch die Nutzung des Bots entstehen. Dies umfasst insbesondere Datenverlust, Serverprobleme oder Einschränkungen durch Discord.",
  },
  {
    title: "5. Datenschutz",
    content: (
      <p>
        Alle gesammelten Daten werden gemäß der{" "}
        <Link to="/datenschutz" className="text-primary hover:underline">
          Datenschutzerklärung
        </Link>{" "}
        von ManagerX verarbeitet. Du bist dafür verantwortlich, die Mitglieder deines Servers über die Nutzung des Bots und die Datenverarbeitung zu informieren.
      </p>
    ),
  },
  {
    title: "6. Rechte an Inhalten",
    content: "Alle von ManagerX bereitgestellten Funktionen, Codes und Datenbanken sind Eigentum von ManagerX Development. Du darfst diese nur im Rahmen der Bot-Nutzung verwenden und nicht für eigene kommerzielle Projekte weitergeben oder kopieren.",
  },
  {
    title: "7. Änderungen der Nutzungsbedingungen",
    content: "ManagerX Development kann diese Nutzungsbedingungen jederzeit ändern. Änderungen werden auf den Discord-Servern oder per Bot-Kommunikation bekanntgegeben. Die fortgesetzte Nutzung von ManagerX gilt als Zustimmung zu den geänderten Bedingungen.",
  },
];

const Nutzungsbedingungen = memo(function Nutzungsbedingungen() {
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
            <FileText className="w-10 h-10 text-primary" />
            <h1 className="text-4xl font-bold">
              <span className="text-gradient">Nutzungsbedingungen</span>
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
              <h2 className="text-xl font-semibold mb-4 text-foreground">8. Kontakt</h2>
              <p className="text-muted-foreground mb-4">
                Bei Fragen zu den Nutzungsbedingungen oder Problemen mit dem Bot:
              </p>
              <a 
                href="mailto:development@oppro-network.de" 
                className="inline-flex items-center gap-2 text-primary hover:underline"
              >
                <Mail className="w-4 h-4" />
                development@oppro-network.de
              </a>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
});

export default Nutzungsbedingungen;
