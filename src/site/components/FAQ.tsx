import { memo } from "react";
import { motion } from "framer-motion";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { HelpCircle, Sparkles } from "lucide-react";

const faqs = [
  {
    question: "Wie füge ich ManagerX zu meinem Server hinzu?",
    answer: "Klicke einfach auf den 'Zum Server hinzufügen' Button oben auf der Seite. Du wirst zu Discord weitergeleitet, wo du den Server auswählen kannst, auf dem du ManagerX installieren möchtest. Stelle sicher, dass du Administrator-Rechte auf diesem Server hast."
  },
  {
    question: "Ist ManagerX kostenlos?",
    answer: "Ja! ManagerX ist vollständig kostenlos nutzbar. Alle Kernfunktionen wie Moderation, Levelsystem, Globalchat und mehr stehen dir ohne Einschränkungen zur Verfügung."
  },
  {
    question: "Wie funktioniert das Levelsystem?",
    answer: "Das Levelsystem vergibt automatisch XP für Nachrichten und Voice-Chat-Aktivität. Du kannst XP-Raten, Level-Rollen und Benachrichtigungen vollständig anpassen. Server-weite und globale Leaderboards zeigen die aktivsten Mitglieder."
  },
  {
    question: "Was ist der Globalchat?",
    answer: "Der Globalchat verbindet deinen Server mit anderen ManagerX-Servern in Echtzeit. Nachrichten werden moderiert und gefiltert. Du hast volle Kontrolle über Blacklists und kannst User blockieren oder reporten."
  },
  {
    question: "Wie kann ich Support erhalten?",
    answer: "Tritt unserem Support-Server bei! Dort findest du eine aktive Community und unser Team, das dir bei allen Fragen hilft. Du kannst auch die Dokumentation und FAQ auf unserer Website nutzen."
  },
  {
    question: "Kann ich die Bot-Befehle anpassen?",
    answer: "Absolut! Du kannst Präfixe ändern, Befehle aktivieren/deaktivieren, Berechtigungen für bestimmte Rollen festlegen und vieles mehr. Die meisten Einstellungen sind über das Dashboard oder Slash-Commands konfigurierbar."
  },
];

export const FAQ = memo(function FAQ() {
  return (
    <section id="faq" className="relative py-32 overflow-hidden">
      {/* Simple Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-primary/5 to-background" />

      <div className="container relative z-10 px-4">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 glass rounded-full px-5 py-2.5 mb-6">
            <HelpCircle className="w-4 h-4 text-accent" />
            <span className="text-sm text-foreground/80 font-medium">Häufige Fragen</span>
          </div>

          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="text-foreground">Hast du </span>
            <span className="relative">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent font-extrabold">Fragen</span>
              <Sparkles className="absolute -top-2 -right-6 w-5 h-5 text-accent" />
            </span>
            <span className="text-foreground">?</span>
          </h2>
          <p className="text-xl text-foreground/70 max-w-2xl mx-auto">
            Hier findest du Antworten auf die häufigsten Fragen zu ManagerX.
          </p>
        </motion.div>

        {/* FAQ Accordion */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="max-w-3xl mx-auto"
        >
          <Accordion type="single" collapsible className="space-y-4">
            {faqs.map((faq, index) => (
              <AccordionItem
                key={index}
                value={`item-${index}`}
                className="glass rounded-2xl px-6 border-0 overflow-hidden hover:bg-card/80 transition-colors duration-300"
              >
                <AccordionTrigger className="text-left text-lg font-semibold text-foreground hover:no-underline py-5 [&[data-state=open]]:text-primary">
                  <span className="flex items-center gap-3">
                    <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-sm font-bold text-primary">
                      {index + 1}
                    </span>
                    {faq.question}
                  </span>
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground text-base leading-relaxed pb-5 pl-11">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </motion.div>
      </div>
    </section>
  );
});
