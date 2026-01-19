import { memo } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Mail, MapPin, User } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

const Impressum = memo(function Impressum() {
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
          <h1 className="text-4xl font-bold mb-2">
            <span className="text-gradient">Impressum</span>
          </h1>
          <p className="text-muted-foreground mb-12">Angaben gemäß § 5 TMG</p>

          <div className="glass rounded-2xl p-8 space-y-8">
            <section className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <User className="w-5 h-5 text-primary" />
                </div>
                <h2 className="text-xl font-semibold">Verantwortlich</h2>
              </div>
              <div className="pl-13 space-y-1 text-muted-foreground">
                <p className="text-foreground font-medium">Lenny Steiger</p>
              </div>
            </section>

            <section className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <MapPin className="w-5 h-5 text-primary" />
                </div>
                <h2 className="text-xl font-semibold">Anschrift</h2>
              </div>
              <div className="pl-13 space-y-1 text-muted-foreground">
                <p>Eulauer Str. 24</p>
                <p>04523 Pegau</p>
                <p>Deutschland</p>
              </div>
            </section>

            <section className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Mail className="w-5 h-5 text-primary" />
                </div>
                <h2 className="text-xl font-semibold">Kontakt</h2>
              </div>
              <div className="pl-13">
                <a 
                  href="mailto:contact@oppro-network.de" 
                  className="text-primary hover:underline"
                >
                  contact@oppro-network.de
                </a>
              </div>
            </section>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
});

export default Impressum;
