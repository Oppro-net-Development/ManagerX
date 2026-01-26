import { memo } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Code2, GitBranch, Heart, ExternalLink, Shield } from "lucide-react";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";

export const License = memo(function License() {
  // Python Dependencies
  const pythonDependencies = [
    { name: "py-cord", version: "2.7.0", license: "MIT", url: "https://github.com/Pycord-Development/pycord" },
    { name: "ezcord", version: "0.7.4", license: "MIT", url: "https://github.com/ezcord-org/ezcord" },
    { name: "aiosqlite", version: "0.22.1", license: "MIT", url: "https://github.com/omnilib/aiosqlite" },
    { name: "aiohttp", version: "3.13.3", license: "Apache 2.0", url: "https://github.com/aio-libs/aiohttp" },
    { name: "aiocache", version: "0.12.3", license: "BSD", url: "https://github.com/aio-libs/aiocache" },
    { name: "propcache", version: "0.4.1", license: "Apache 2.0", url: "https://github.com/async-http-client/propcache" },
    { name: "requests", version: "2.32.5", license: "Apache 2.0", url: "https://github.com/psf/requests" },
    { name: "wikipedia", version: "1.4.0", license: "MIT", url: "https://github.com/goldsmith/Wikipedia" },
    { name: "beautifulsoup4", version: "4.14.3", license: "MIT", url: "https://www.crummy.com/software/BeautifulSoup/" },
    { name: "soupsieve", version: "2.8.1", license: "MIT", url: "https://github.com/facelessuser/soupsieve" },
    { name: "yarl", version: "1.22.0", license: "Apache 2.0", url: "https://github.com/aio-libs/yarl" },
    { name: "frozenlist", version: "1.8.0", license: "Apache 2.0", url: "https://github.com/aio-libs/frozenlist" },
    { name: "multidict", version: "6.7.0", license: "Apache 2.0", url: "https://github.com/aio-libs/multidict" },
    { name: "h11", version: "0.16.0", license: "MIT", url: "https://github.com/python-hyper/h11" }
  ];

  // Node.js/JavaScript Dependencies
  const nodeDependencies = [
    { name: "react", version: "18+", license: "MIT", url: "https://github.com/facebook/react" },
    { name: "typescript", version: "5+", license: "Apache 2.0", url: "https://github.com/microsoft/TypeScript" },
    { name: "vite", version: "5+", license: "MIT", url: "https://github.com/vitejs/vite" },
    { name: "tailwindcss", version: "3.4+", license: "MIT", url: "https://github.com/tailwindlabs/tailwindcss" },
    { name: "@radix-ui/*", version: "latest", license: "MIT", url: "https://github.com/radix-ui/primitives" },
    { name: "framer-motion", version: "12+", license: "MIT", url: "https://github.com/framer/motion" },
    { name: "react-router-dom", version: "6+", license: "MIT", url: "https://github.com/remix-run/react-router" },
    { name: "lucide-react", version: "latest", license: "ISC", url: "https://github.com/lucide-icons/lucide" }
  ];

  // Other Dependencies (Tools & Databases)
  const otherDependencies = [
    { name: "sphinx", version: "latest", license: "BSD", url: "https://github.com/sphinx-doc/sphinx" },
    { name: "SQLite", version: "3+", license: "Public Domain", url: "https://www.sqlite.org" }
  ];

  // License Card Component
  const LicenseCard = ({ dep, index }: { dep: any; index: number }) => (
    <motion.a
      href={dep.url}
      target="_blank"
      rel="noopener noreferrer"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      className="group bg-secondary/30 hover:bg-secondary/50 rounded-xl p-4 border border-white/5 hover:border-primary/30 transition-all"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
            {dep.name}
          </h3>
          <p className="text-xs text-muted-foreground mt-1">v{dep.version}</p>
          <p className="text-xs text-muted-foreground mt-1.5">
            <span className="inline-block px-2 py-0.5 rounded bg-primary/10 text-primary font-mono text-[9px]">
              {dep.license}
            </span>
          </p>
        </div>
        <ExternalLink className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0 opacity-0 group-hover:opacity-100 mt-1" />
      </div>
    </motion.a>
  );

  return (
    <div 
      className="min-h-screen bg-background flex flex-col"
    >
      <Navbar />
      
      <main className="flex-grow container relative z-10 px-4 pt-32 pb-24">
        <div className="max-w-5xl mx-auto">
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

          {/* Header */}
          <header className="mb-12">
            <div className="flex items-center gap-5 mb-4">
              <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20">
                <Code2 className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="text-4xl font-black tracking-tight text-foreground uppercase">
                  Open <span className="text-primary">Source</span>
                </h1>
                <p className="text-muted-foreground font-mono text-[10px] uppercase tracking-widest mt-1 opacity-50">
                  GPL-3.0 & Lizenz Information
                </p>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass rounded-3xl p-8 md:p-12 border border-white/5 space-y-12"
          >
            {/* GPL-3.0 License Section */}
            <section className="space-y-6">
              <div className="flex items-center gap-3">
                <Shield className="w-6 h-6 text-primary" />
                <h2 className="text-2xl font-bold text-foreground">GNU General Public License v3.0</h2>
              </div>
              
              <div className="bg-secondary/50 rounded-2xl p-6 border border-primary/10 space-y-4">
                <p className="text-foreground">
                  <strong>ManagerX</strong> ist lizenziert unter der{" "}
                  <a 
                    href="https://www.gnu.org/licenses/gpl-3.0.de.html" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    GNU General Public License v3.0 (GPL-3.0)
                  </a>
                </p>

                <div className="space-y-3 text-sm text-muted-foreground">
                  <div className="flex items-start gap-3">
                    <span className="text-primary font-bold mt-0.5">✓</span>
                    <p><strong>Freiheit zu verwenden:</strong> Sie können das Programm für jeden Zweck verwenden.</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-primary font-bold mt-0.5">✓</span>
                    <p><strong>Freiheit zu studieren:</strong> Sie können den Quellcode einsehen und verstehen.</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-primary font-bold mt-0.5">✓</span>
                    <p><strong>Freiheit zu verteilen:</strong> Sie können Kopien weitergeben.</p>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-primary font-bold mt-0.5">✓</span>
                    <p><strong>Freiheit zu verbessern:</strong> Sie können das Programm modifizieren und verbesserungen veröffentlichen.</p>
                  </div>
                </div>

                <div className="pt-4 border-t border-white/10">
                  <p className="text-xs text-muted-foreground">
                    <strong>Wichtig:</strong> Modifizierte Versionen müssen auch unter GPL-3.0 veröffentlicht werden. Der Quellcode muss verfügbar sein.
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap gap-3">
                <a
                  href="https://www.gnu.org/licenses/gpl-3.0.de.html"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-colors text-sm font-medium border border-primary/20"
                >
                  <ExternalLink className="w-4 h-4" />
                  GPL-3.0 Lizenz
                </a>
                <a
                  href="https://github.com/ManagerX-Development/ManagerX/blob/main/LICENSE"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-accent/10 text-accent hover:bg-accent/20 transition-colors text-sm font-medium border border-accent/20"
                >
                  <GitBranch className="w-4 h-4" />
                  GitHub LICENSE
                </a>
              </div>
            </section>

            {/* Python Dependencies Section */}
            <section className="space-y-6 pt-8 border-t border-white/10">
              <div className="flex items-center gap-3">
                <Code2 className="w-6 h-6 text-success" />
                <h2 className="text-2xl font-bold text-foreground">Python Abhängigkeiten</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {pythonDependencies.map((dep, i) => (
                  <LicenseCard key={dep.name} dep={dep} index={i} />
                ))}
              </div>
            </section>

            {/* Node.js Dependencies Section */}
            <section className="space-y-6 pt-8 border-t border-white/10">
              <div className="flex items-center gap-3">
                <Code2 className="w-6 h-6 text-info" />
                <h2 className="text-2xl font-bold text-foreground">Node.js Abhängigkeiten</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {nodeDependencies.map((dep, i) => (
                  <LicenseCard key={dep.name} dep={dep} index={i} />
                ))}
              </div>
            </section>

            {/* Other Dependencies Section */}
            <section className="space-y-6 pt-8 border-t border-white/10">
              <div className="flex items-center gap-3">
                <Code2 className="w-6 h-6 text-warning" />
                <h2 className="text-2xl font-bold text-foreground">Weitere Abhängigkeiten</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {otherDependencies.map((dep, i) => (
                  <LicenseCard key={dep.name} dep={dep} index={i} />
                ))}
              </div>
            </section>

            {/* Contributing Section */}
            <section className="space-y-6 pt-8 border-t border-white/10">
              <div className="flex items-center gap-3">
                <Heart className="w-6 h-6 text-accent" />
                <h2 className="text-2xl font-bold text-foreground">Mitentwicklung</h2>
              </div>
              <div className="bg-secondary/50 rounded-2xl p-6 border border-accent/10">
                <div className="space-y-3 text-sm text-muted-foreground">
                  <p>• Bug-Reports und Verbesserungsvorschläge</p>
                  <p>• Code-Beiträge und Feature-Implementationen</p>
                  <p>• Dokumentations-Verbesserungen</p>
                </div>
                <div className="mt-6">
                  <a
                    href="https://github.com/ManagerX-Development/ManagerX/blob/main/CONTRIBUTING.md"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-accent/10 text-accent hover:bg-accent/20 transition-colors text-sm font-medium border border-accent/20"
                  >
                    <GitBranch className="w-4 h-4" />
                    Contribution Guidelines
                  </a>
                </div>
              </div>
            </section>

            {/* Copyright Section */}
            <section className="space-y-6 pt-8 border-t border-white/10">
              <h2 className="text-xl font-bold text-foreground">Copyright & Attribution</h2>
              <div className="bg-secondary/50 rounded-2xl p-6 border border-white/10 space-y-2 text-sm text-muted-foreground">
                <p>© 2026 ManagerX Development</p>
                <p>© 2024-2026 OPPRO.NET Network</p>
                <p>GPL-3.0 Open Source Project</p>
              </div>
            </section>

            {/* Links Section */}
            <section className="space-y-4 pt-8 border-t border-white/10">
              <h3 className="text-sm font-semibold text-muted-foreground uppercase">Links</h3>
              <div className="flex flex-wrap gap-4">
                <Link to="/datenschutz" className="text-xs text-primary hover:underline">Datenschutz</Link>
                <Link to="/nutzungsbedingungen" className="text-xs text-primary hover:underline">Nutzungsbedingungen</Link>
                <Link to="/impressum" className="text-xs text-primary hover:underline">Impressum</Link>
                <a href="https://github.com/ManagerX-Development/ManagerX" target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline">GitHub</a>
              </div>
            </section>
          </motion.div>
        </div>
      </main>

      <Footer />
    </div>
  );
});

export default License;
