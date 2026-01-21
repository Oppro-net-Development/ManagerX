import { memo, useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { 
  ArrowLeft, Activity, Globe, Cpu, Layers, 
  CheckCircle2, XCircle, Mail, Github 
} from "lucide-react";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";

const Status = memo(function Status() {
  // State für die Live-Daten vom Bot
  const [data, setData] = useState({ 
    status: "loading", 
    latency: "--", 
    version: "2.0.0",
    guilds: 0 
  });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        // Abfrage an deinen Py-cord Bot auf Port 8040
        const response = await fetch("http://localhost:8040/api/status");
        if (!response.ok) throw new Error("Offline");
        
        const result = await response.json();
        setData({
          status: "online",
          latency: result.latency,
          version: result.version,
          guilds: result.guilds
        });
      } catch (error) {
        // Falls der Bot nicht erreichbar ist
        setData((prev) => ({ ...prev, status: "offline", latency: "--" }));
      }
    };

    fetchStatus();
    // Alle 15 Sekunden aktualisieren
    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const systems = [
    {
      name: "ManagerX Core Engine",
      status: data.status,
      latency: data.latency,
      description: `Zentrale Instanz (v${data.version}) inkl. KI & SQLite`,
      icon: Cpu,
      isParent: true
    },
    {
      name: "Globalchat Network",
      status: data.status === "online" ? "online" : "offline",
      latency: "Active",
      description: "Echtzeit-Verbindung zum ManagerX-Netzwerk",
      icon: Globe,
    },
    {
      name: "Static Content",
      status: "online", // Website läuft ja gerade
      latency: "2ms",
      description: "Bereitstellung von lokalen Modul-Assets",
      icon: Layers,
    }
  ];

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar />
      
      <main className="flex-grow container relative z-10 px-4 pt-32 pb-24 text-white">
        <div className="max-w-4xl mx-auto">
          
          <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}>
            <Link to="/" className="inline-flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors mb-12 group text-sm font-medium">
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
              Zurück zur Zentrale
            </Link>
          </motion.div>

          <header className="mb-16 text-center md:text-left">
            <div className="flex flex-col md:flex-row items-center gap-5 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20">
                <Activity className={cn(
                  "w-6 h-6 transition-all",
                  data.status === "online" ? "text-primary animate-pulse" : "text-red-500"
                )} />
              </div>
              <div>
                <h1 className="text-4xl font-black tracking-tight text-foreground uppercase italic">
                  System <span className="text-primary">Status</span>
                </h1>
                <div className="flex items-center justify-center md:justify-start gap-3 mt-1">
                  <span className="relative flex h-2 w-2">
                    <span className={cn(
                      "absolute inline-flex h-full w-full rounded-full opacity-75",
                      data.status === "online" ? "animate-ping bg-green-400" : "bg-red-400"
                    )}></span>
                    <span className={cn(
                      "relative inline-flex rounded-full h-2 w-2",
                      data.status === "online" ? "bg-green-500" : "bg-red-500"
                    )}></span>
                  </span>
                  <span className={cn(
                    "text-[10px] font-mono uppercase tracking-[0.2em]",
                    data.status === "online" ? "text-green-500/80" : "text-red-500/80"
                  )}>
                    {data.status === "online" ? "Alle Systeme stabil" : "Verbindung zum Core unterbrochen"}
                  </span>
                </div>
              </div>
            </div>
          </header>

          <div className="grid gap-4 mb-16">
            {systems.map((system, index) => (
              <motion.div 
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={cn(
                  "glass rounded-2xl p-6 border flex flex-col md:flex-row items-center justify-between gap-6 relative",
                  system.status === "online" ? "border-white/5" : "border-red-500/20 bg-red-500/[0.02]",
                  system.isParent && system.status === "online" ? "border-primary/20 bg-primary/[0.01]" : ""
                )}
              >
                <div className="flex items-center gap-5 w-full">
                  <div className={cn(
                    "w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center",
                    system.status === "online" ? "text-primary" : "text-red-500"
                  )}>
                    <system.icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold">{system.name}</h3>
                    <p className="text-xs text-muted-foreground">{system.description}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between md:justify-end w-full md:w-auto gap-8">
                  <div className="text-right hidden md:block font-mono">
                    <p className="text-[10px] text-muted-foreground/50 uppercase tracking-tighter">Ping / Stats</p>
                    <p className="text-sm text-primary">
                      {system.isParent && data.status === "online" ? `${data.latency}` : system.latency}
                    </p>
                  </div>
                  
                  <div className={cn(
                    "px-4 py-2 rounded-xl border flex items-center gap-2 min-w-[110px] justify-center",
                    system.status === "online" 
                      ? "bg-green-500/10 border-green-500/20 text-green-500" 
                      : "bg-red-500/10 border-red-500/20 text-red-500"
                  )}>
                    {system.status === "online" ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                    <span className="text-[10px] font-black uppercase tracking-widest">{system.status}</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Footer Info */}
          <div className="mt-20 flex flex-col md:flex-row items-center justify-between p-8 glass rounded-3xl border border-white/5 gap-6">
            <div className="text-center md:text-left text-sm text-muted-foreground">
              <p>Aktive Gilden im Netzwerk: <span className="text-white font-mono">{data.guilds}</span></p>
              <p>Überprüfung erfolgt alle 15 Sekunden via Local-API.</p>
            </div>
            <div className="flex gap-3">
              <a href="mailto:support@oppro.net" className="p-3 glass rounded-xl hover:text-primary transition-colors border border-white/5">
                <Mail className="w-5 h-5" />
              </a>
              <a href="https://github.com/ManagerX-Development" className="p-3 glass rounded-xl hover:text-primary transition-colors border border-white/5">
                <Github className="w-5 h-5" />
              </a>
            </div>
          </div>

        </div>
      </main>

      <Footer />
    </div>
  );
});

// Hilfsfunktion für Tailwind-Klassen (falls nicht vorhanden, einfach weglassen oder durch Template Strings ersetzen)
function cn(...classes: any[]) {
  return classes.filter(Boolean).join(" ");
}

export default Status;