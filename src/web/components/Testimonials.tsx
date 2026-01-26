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
    whileHover={{ y: -8 }}
    className="glass rounded-2xl p-8 hover:bg-card/80 transition-all duration-300 border border-white/10 backdrop-blur-lg"
  >
    <div className="flex gap-1 mb-6">
      {[...Array(testimonial.rating)].map((_, i) => (
        <Star key={i} className="w-4 h-4 fill-accent text-accent" />
      ))}
    </div>

    <p className="text-foreground/90 mb-8 italic text-lg leading-relaxed">
      "{testimonial.text}"
    </p>

    <div className="flex items-center gap-3 mb-4">
      <motion.div 
        whileHover={{ scale: 1.1 }}
        className="w-12 h-12 rounded-full bg-gradient-to-br from-primary/80 to-accent/80 flex items-center justify-center text-primary-foreground font-bold text-base shadow-lg shadow-primary/30"
      >
        {testimonial.avatar}
      </motion.div>
      <div className="flex-1">
        <div className="font-bold text-base text-foreground">{testimonial.name}</div>
        <div className="text-sm text-muted-foreground font-medium">{testimonial.role}</div>
      </div>
    </div>

    <div className="pt-4 border-t border-white/10 flex items-center justify-between text-[12px] uppercase tracking-wider font-bold text-muted-foreground/70">
      <span>{testimonial.server}</span>
      <span className="flex items-center gap-1.5 text-accent">
        <Users className="w-3.5 h-3.5" />
        {testimonial.members} Member
      </span>
    </div>
  </motion.div>
));

export const Testimonials = memo(function Testimonials() {
  return (
    <section id="testimonials" className="relative py-32 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-background via-primary/8 to-background" />
      <div className="absolute top-0 left-1/3 w-[500px] h-[500px] bg-primary/10 blur-[150px] rounded-full" />
      <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-accent/10 blur-[150px] rounded-full" />

      <div className="container relative z-10 px-4">
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
            transition={{ duration: 0.6, ease: "easeInOut" }}
            className="inline-flex items-center gap-2 glass rounded-full px-6 py-3 mb-8 border border-accent/20"
          >
            <TrendingUp className="w-4 h-4 text-accent" />
            <span className="text-xs text-foreground/80 font-bold tracking-widest uppercase">Early Access Feedback</span>
          </motion.div>

          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1, duration: 0.7, ease: "easeInOut" }}
            className="text-5xl md:text-6xl font-black mb-6 tracking-tighter"
          >
            Stimmen der <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">Ersten Stunde</span>
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed font-medium"
          >
            Admins, die ManagerX von Anfang an begleiten, teilen ihre Erfahrungen.
          </motion.p>
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