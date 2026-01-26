import { memo } from "react";
import { motion } from "framer-motion";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { HelpCircle, Sparkles, Terminal, ShieldCheck, Github, Layout } from "lucide-react";

const faqs = [
  {
    question: "Warum V2.0.0 und was hat sich geändert?",
    answer: "Die V2 ist ein kompletter Rewrite der Kern-Architektur. Wir haben das System auf 90 hochperformante Slash-Commands optimiert, um Redundanzen zu vermeiden. Das Ergebnis ist ein sauberer Sync mit der Discord-API ohne doppelte Befehle oder Verzögerungen."
  },
  {
    question: "Ist ManagerX Open Source und welche Lizenz wird genutzt?",
    answer: "Ja! ManagerX ist vollständig Open Source und wird transparent auf GitHub unter 'ManagerX Development' entwickelt. Das Projekt steht unter der GPL-3.0 Lizenz, was bedeutet, dass der Code frei bleibt und die Rechte der Community dauerhaft geschützt sind."
  },
  {
    question: "Kann man ManagerX selbst hosten?",
    answer: "Absolut. Dank der ressourcensparenden V2-Architektur läuft ManagerX extrem effizient. Er kann problemlos auf kleinen Instanzen oder sogar Free-Hosting-Servern betrieben werden, ohne an Performance bei den 90 Commands einzubüßen."
  },
  {
    question: "Wie steht es um die Sicherheit?",
    answer: "Sicherheit ist in der V2 fest verankert. Durch die ausschließliche Nutzung von Slash-Commands können Berechtigungen direkt über die Discord-Integration verwaltet werden. Da der Code Open Source ist, kann zudem jeder die Sicherheitsstandards im Repository einsehen."
  },
  {
    question: "Ist ManagerX kostenlos?",
    answer: "Ja, ManagerX ist und bleibt kostenlos. Sowohl die Nutzung unseres öffentlichen Bots als auch der Zugriff auf den Quellcode für das Self-Hosting sind ohne Kosten verbunden."
  },
  {
    question: "Wie funktioniert das Levelsystem in der V2?",
    answer: "Das XP-System wurde für die V2 komplett optimiert. Es trackt Text- und Voice-Aktivität zuverlässiger und bietet eine stabile Basis für serverübergreifende Leaderboards, die aktuell im Rahmen der V2-Entwicklung ausgebaut werden."
  },
  {
    question: "Wo finde ich Hilfe oder Support?",
    answer: "Mit aktuell 16 Servern bieten wir sehr persönlichen Support. Du kannst unserem Discord-Server beitreten oder direkt im GitHub-Repository unter 'ManagerX-Development/ManagerX' Issues erstellen, falls du technische Fragen hast."
  }
];

export const FAQ = memo(function FAQ() {
  return (
    <section id="faq" className="relative py-32 overflow-hidden">
      {/* Premium Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-accent/5 to-primary/5" />
      <div className="absolute top-1/3 right-0 w-[600px] h-[600px] bg-primary/10 blur-[150px] rounded-full" />
      <div className="absolute bottom-0 left-1/4 w-[500px] h-[500px] bg-accent/10 blur-[150px] rounded-full" />

      <div className="container relative z-10 px-4">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, ease: "easeInOut" }}
          className="text-center mb-20"
        >
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-3 glass rounded-full px-6 py-3 mb-8 border border-accent/20"
          >
            <Terminal className="w-4 h-4 text-accent" />
            <span className="text-xs font-mono font-bold text-foreground/80 uppercase tracking-tighter">
              V2.0.0 • 90 Commands • GPL-3.0
            </span>
          </motion.div>

          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-5xl md:text-6xl font-black mb-6 tracking-tighter"
          >
            Häufige <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">Fragen</span>
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed font-medium"
          >
            Alles Wissenswerte über die Open-Source-Entwicklung, das Self-Hosting und die neue V2-Architektur.
          </motion.p>
        </motion.div>

        {/* FAQ Accordion */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-3xl mx-auto"
        >
          <Accordion type="single" collapsible className="space-y-3">
            {faqs.map((faq, index) => (
              <AccordionItem
                key={index}
                value={`item-${index}`}
                className="glass rounded-2xl px-6 border border-white/5 overflow-hidden hover:bg-white/[0.02] transition-all duration-300"
              >
                <AccordionTrigger className="text-left text-base md:text-lg font-bold text-foreground/90 hover:no-underline py-5 [&[data-state=open]]:text-primary">
                  <span className="flex items-center gap-4">
                    {index === 1 ? (
                      <Github className="w-5 h-5 text-accent/70" />
                    ) : (
                      <ShieldCheck className="w-5 h-5 text-accent/50" />
                    )}
                    {faq.question}
                  </span>
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground text-sm md:text-base leading-relaxed pb-5 pl-9 border-t border-white/5 pt-4">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </motion.div>

        {/* Technical Footer Info */}
        <motion.div 
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          className="mt-16 flex flex-wrap justify-center gap-6 text-[10px] font-mono text-muted-foreground uppercase tracking-[0.2em]"
        >
          <div className="flex items-center gap-1.5 border border-white/5 px-3 py-1 rounded-full bg-white/5">
            <Layout className="w-3 h-3" /> Core: EzCord 0.7.4
          </div>
          <div className="flex items-center gap-1.5 border border-white/5 px-3 py-1 rounded-full bg-white/5">
            <Github className="w-3 h-3" /> Repo: ManagerX-Development
          </div>
          <div className="flex items-center gap-1.5 border border-accent/20 px-3 py-1 rounded-full bg-accent/5 text-accent">
            <ShieldCheck className="w-3 h-3" /> License: GPL-3.0
          </div>
        </motion.div>
      </div>
    </section>
  );
});