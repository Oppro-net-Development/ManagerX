import { memo } from "react";
import { Link } from "react-router-dom";
import { 
  ArrowLeft, Puzzle, Gamepad2, Globe, ShieldCheck, 
  Users, Zap, Settings2, Code2, Layers, Mail, Github 
} from "lucide-react";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";

const corePlugins = [
  {
    title: "AI Entertainment",
    features: ["4-Gewinnt (VS KI)", "TicTacToe (VS KI)"],
    description: "Intelligente Minispiele direkt im Discord-Chat durch moderne KI-Integration.",
    icon: Gamepad2,
  },
  {
    title: "Global Network",
    features: ["Globalchat", "Server-übergreifend"],
    description: "Verbinde deine Community mit dem gesamten ManagerX-Netzwerk weltweit.",
    icon: Globe,
  },
  {
    title: "Security Core",
    features: ["Antispam", "Moderation", "Warn-System", "Notes"],
    description: "Vollständiger Schutz und Verwaltung für dein Team mit intelligenten Filtern.",
    icon: ShieldCheck,
  },
  {
    title: "Social & Engagement",
    features: ["Levelsystem", "Welcome-Engine", "TempVC"],
    description: "Steigere die Aktivität durch Belohnungen und vollautomatische Sprachkanäle.",
    icon: Users,
  },
  {
    title: "Automation",
    features: ["Autodelete", "Autorole", "Loggingsystem"],
    description: "Halte deinen Server sauber und organisiert – alles vollautomatisch im Hintergrund.",
    icon: Zap,
  },
  {
    title: "System Control",
    features: ["Settings", "Stats"],
    description: "Behalte den vollen Überblick mit detaillierten Analysen und einfacher Konfiguration.",
    icon: Settings2,
  }
];

export const PluginsPage = memo(function PluginsPage() {
  return (
    <div 
      className="min-h-screen bg-background flex flex-col"
    >
      <Navbar />
      
      <main className="flex-grow container relative z-10 px-4 pt-32 pb-24">
        <div className="max-w-5xl mx-auto">
          
          {/* Zurück Button */}
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

          {/* Header Bereich */}
          <header className="mb-16">
            <div className="flex items-center gap-5 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20">
                <Puzzle className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="text-4xl font-black tracking-tight text-foreground uppercase">
                  Built-in <span className="text-primary">Modules</span>
                </h1>
                <div className="flex gap-3 mt-1 opacity-40">
                  <span className="text-[10px] font-mono uppercase tracking-widest">Version 2.4.0</span>
                  <span className="text-[10px] font-mono uppercase tracking-widest">•</span>
                  <span className="text-[10px] font-mono uppercase tracking-widest">Native Core</span>
                </div>
              </div>
            </div>
            <p className="text-muted-foreground max-w-2xl leading-relaxed">
              ManagerX ist modular aufgebaut. Die folgenden Kern-Module sind bereits vorinstalliert und können über das Dashboard konfiguriert werden.
            </p>
          </header>

          {/* Core Plugins Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-24">
            {corePlugins.map((plugin, index) => (
              <motion.div 
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.05 }}
                className="glass rounded-2xl p-8 border border-white/5 hover:border-primary/10 transition-colors flex flex-col"
              >
                <div className="flex items-start justify-between mb-6">
                  <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-primary">
                    <plugin.icon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono text-primary/40 uppercase tracking-tighter">Module 0{index + 1}</span>
                </div>
                
                <h2 className="text-lg font-bold mb-3 text-white">{plugin.title}</h2>
                <p className="text-sm text-muted-foreground leading-relaxed mb-6">
                  {plugin.description}
                </p>

                <div className="flex flex-wrap gap-2 mt-auto">
                  {plugin.features.map(f => (
                    <span key={f} className="text-[9px] font-mono bg-white/5 border border-white/10 text-white/50 px-2 py-1 rounded lowercase">
                      #{f.replace(/\s+/g, '_')}
                    </span>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>

          {/* External Section - Dezent wie Kontaktbereich */}
          <div className="pt-12 border-t border-white/5">
            <div className="flex items-center gap-3 mb-8">
              <Layers className="w-5 h-5 text-primary/50" />
              <h2 className="text-xl font-bold uppercase tracking-tight">External Marketplace</h2>
              <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-mono animate-pulse">COMING SOON</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-8 rounded-3xl border border-dashed border-white/10 bg-white/[0.01] flex flex-col gap-4">
                <Code2 className="w-6 h-6 text-muted-foreground" />
                <h3 className="font-bold">Developer SDK</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Erstelle eigene Python-Module und integriere sie nahtlos in das ManagerX Ökosystem.
                </p>
              </div>
              <div className="p-8 rounded-3xl border border-dashed border-white/10 bg-white/[0.01] flex flex-col gap-4">
                <Github className="w-6 h-6 text-muted-foreground" />
                <h3 className="font-bold">Community Library</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Teile deine Plugins mit der Community oder entdecke Module von anderen Entwicklern.
                </p>
              </div>
            </div>
          </div>

          {/* Kontakt / Support Footer wie in Legal-Seiten */}
          <motion.div 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            className="mt-24 p-8 rounded-3xl border border-white/5 bg-white/[0.02] flex flex-col md:flex-row items-center justify-between gap-6"
          >
            <div className="text-center md:text-left">
              <h3 className="font-bold text-white">Modul-Wunsch?</h3>
              <p className="text-sm text-muted-foreground">Kontaktiere uns für individuelle Funktions-Ideen.</p>
            </div>
            <div className="flex gap-4">
              <a href="mailto:development@oppro-network.de" className="p-3 rounded-xl glass border border-white/10 hover:text-primary transition-colors" title="Email">
                <Mail className="w-5 h-5" />
              </a>
              <a href="https://github.com/ManagerX-Development/ManagerX" className="p-3 rounded-xl glass border border-white/10 hover:text-primary transition-colors" title="GitHub">
                <Github className="w-5 h-5" />
              </a>
            </div>
          </motion.div>

        </div>
      </main>

      <Footer />
    </div>
  );
});

export default PluginsPage;