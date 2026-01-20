import { memo } from "react";
import { motion } from "framer-motion";
import { Star, MessageSquare, Users, TrendingUp } from "lucide-react";

const testimonials = [
  {
    name: "Lukas",
    role: "Server Owner",
    server: "Small Talk Central",
    members: "42",
    avatar: "L",
    rating: 5,
    text: "Einer der ersten 10 Server zu sein hat Vorteile! Der Entwickler hört direkt auf Feedback. Das Levelsystem ist schon jetzt besser als bei den großen Bots.",
  },
  {
    name: "Marcel",
    role: "Admin",
    server: "Dev Corner",
    members: "112",
    avatar: "M",
    rating: 5,
    text: "ManagerX ist zwar noch jung, aber extrem stabil. Endlich mal kein überladener Bot, sondern Fokus auf das, was wir wirklich brauchen.",
  },
  {
    name: "Svenja",
    role: "Moderatorin",
    server: "Chill & Game",
    members: "85",
    avatar: "S",
    rating: 4,
    text: "Wir nutzen ManagerX für unsere Temporary Voice Channels. Funktioniert super intuitiv und das Setup war in 2 Minuten erledigt.",
  },
];

const TestimonialCard = memo(({ testimonial, index }: { testimonial: typeof testimonials[0]; index: number }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: "-50px" }}
    transition={{ duration: 0.4, delay: index * 0.1 }}
    className="glass rounded-2xl p-6 hover:bg-card/80 transition-all duration-300 border border-border/50"
  >
    <div className="flex gap-1 mb-4">
      {[...Array(testimonial.rating)].map((_, i) => (
        <Star key={i} className="w-3.5 h-3.5 fill-accent text-accent" />
      ))}
    </div>

    <p className="text-foreground/90 mb-6 italic leading-relaxed">
      "{testimonial.text}"
    </p>

    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary/80 to-accent/80 flex items-center justify-center text-primary-foreground font-bold text-sm">
        {testimonial.avatar}
      </div>
      <div className="flex-1">
        <div className="font-semibold text-sm text-foreground">{testimonial.name}</div>
        <div className="text-xs text-muted-foreground">{testimonial.role}</div>
      </div>
    </div>

    <div className="mt-4 pt-4 border-t border-border/30 flex items-center justify-between text-[11px] uppercase tracking-wider font-medium text-muted-foreground/70">
      <span>{testimonial.server}</span>
      <span className="flex items-center gap-1">
        <Users className="w-3 h-3" />
        {testimonial.members} Member
      </span>
    </div>
  </motion.div>
));

export const Testimonials = memo(function Testimonials() {
  return (
    <section id="testimonials" className="relative py-24 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-background via-primary/5 to-background" />

      <div className="container relative z-10 px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 glass rounded-full px-4 py-1.5 mb-6 border border-accent/20">
            <TrendingUp className="w-3.5 h-3.5 text-accent" />
            <span className="text-xs text-foreground/80 font-semibold tracking-wide uppercase">Early Access Feedback</span>
          </div>

          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Stimmen der <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">Ersten Stunde</span>
          </h2>
          <p className="text-lg text-foreground/60 max-w-xl mx-auto">
            Wir wachsen langsam, aber stetig. Das sagen die Admins, die ManagerX von Anfang an begleiten.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {testimonials.map((testimonial, index) => (
            <TestimonialCard key={index} testimonial={testimonial} index={index} />
          ))}
        </div>

        {/* Reale Statistiken */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="mt-16 glass rounded-2xl p-6 border border-border/50 max-w-3xl mx-auto"
        >
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center border-r border-border/50">
              <div className="text-2xl font-bold text-foreground">16</div>
              <div className="text-[10px] uppercase tracking-tighter text-muted-foreground">Aktive Server</div>
            </div>
            <div className="text-center border-r border-border/50">
              <div className="text-2xl font-bold text-foreground">~300</div>
              <div className="text-[10px] uppercase tracking-tighter text-muted-foreground">Nutzer</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-accent">100%</div>
              <div className="text-[10px] uppercase tracking-tighter text-muted-foreground">Leidenschaft</div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
});