import { memo } from "react";
import { motion } from "framer-motion";
import { Star, MessageSquare, Users } from "lucide-react";

const testimonials = [
  {
    name: "Max Mustermann",
    role: "Server Admin",
    server: "Gaming Community DE",
    members: "15.000+",
    avatar: "M",
    rating: 5,
    text: "ManagerX hat unseren Server komplett transformiert. Das Levelsystem motiviert unsere Mitglieder unglaublich und die Moderation ist ein Traum!",
  },
  {
    name: "Sarah Schmidt",
    role: "Community Manager",
    server: "Creative Hub",
    members: "8.000+",
    avatar: "S",
    rating: 5,
    text: "Der Globalchat verbindet uns mit anderen Communities - das ist einzigartig! Und der Support ist super schnell und hilfsbereit.",
  },
  {
    name: "Tom Weber",
    role: "Gründer",
    server: "Tech Talk Germany",
    members: "25.000+",
    avatar: "T",
    rating: 5,
    text: "Wir haben viele Bots getestet, aber ManagerX ist der beste. Alle Features funktionieren perfekt zusammen und die Konfiguration ist super einfach.",
  },
  {
    name: "Lisa Müller",
    role: "Moderatorin",
    server: "Anime World",
    members: "12.000+",
    avatar: "L",
    rating: 5,
    text: "Das Anti-Spam System und die Moderations-Tools machen meinen Job so viel einfacher. Endlich ein Bot, der wirklich durchdacht ist!",
  },
  {
    name: "Jan Hoffmann",
    role: "Server Owner",
    server: "Music Lounge",
    members: "5.000+",
    avatar: "J",
    rating: 5,
    text: "Die Temporary Voice Channels sind genial! Unsere Mitglieder lieben es, eigene Räume erstellen zu können. Absolute Empfehlung!",
  },
  {
    name: "Emma Fischer",
    role: "Admin Team Lead",
    server: "Study Together",
    members: "20.000+",
    avatar: "E",
    rating: 5,
    text: "ManagerX ist stabil, schnell und hat alles was wir brauchen. Das Dashboard ist übersichtlich und die Docs sind hervorragend.",
  },
];

const TestimonialCard = memo(({ testimonial, index }: { testimonial: typeof testimonials[0]; index: number }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: "-50px" }}
    transition={{ duration: 0.4, delay: index * 0.05 }}
    className="glass rounded-2xl p-6 hover:bg-card/80 transition-colors duration-300"
  >
    {/* Stars */}
    <div className="flex gap-1 mb-4">
      {[...Array(testimonial.rating)].map((_, i) => (
        <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
      ))}
    </div>

    {/* Text */}
    <p className="text-foreground/90 mb-6 leading-relaxed">
      "{testimonial.text}"
    </p>

    {/* Author */}
    <div className="flex items-center gap-4">
      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-primary-foreground font-bold text-lg">
        {testimonial.avatar}
      </div>
      <div className="flex-1">
        <div className="font-semibold text-foreground">{testimonial.name}</div>
        <div className="text-sm text-muted-foreground">{testimonial.role}</div>
      </div>
    </div>

    {/* Server Info */}
    <div className="mt-4 pt-4 border-t border-border/50 flex items-center justify-between text-sm">
      <span className="text-muted-foreground">{testimonial.server}</span>
      <span className="flex items-center gap-1 text-accent">
        <Users className="w-3.5 h-3.5" />
        {testimonial.members}
      </span>
    </div>
  </motion.div>
));

TestimonialCard.displayName = "TestimonialCard";

export const Testimonials = memo(function Testimonials() {
  return (
    <section id="testimonials" className="relative py-32 overflow-hidden">
      {/* Simple Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-accent/5 to-background" />

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
            <MessageSquare className="w-4 h-4 text-accent" />
            <span className="text-sm text-foreground/80 font-medium">Testimonials</span>
          </div>

          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="text-foreground">Was unsere </span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent font-extrabold">Community</span>
            <span className="text-foreground"> sagt</span>
          </h2>
          <p className="text-xl text-foreground/70 max-w-2xl mx-auto">
            Tausende Server-Admins vertrauen ManagerX. Hier sind ihre Erfahrungen.
          </p>
        </motion.div>

        {/* Testimonials Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {testimonials.map((testimonial, index) => (
            <TestimonialCard key={index} testimonial={testimonial} index={index} />
          ))}
        </div>

        {/* Stats Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="mt-16 glass rounded-2xl p-8 flex flex-wrap justify-center gap-12"
        >
          {[
            { value: "4.9/5", label: "Durchschnittliche Bewertung", icon: Star },
            { value: "10.000+", label: "Zufriedene Server", icon: Users },
            { value: "99%", label: "Würden uns empfehlen", icon: MessageSquare },
          ].map((stat, index) => (
            <div key={index} className="text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <stat.icon className="w-5 h-5 text-accent" />
                <span className="text-3xl font-bold text-foreground">{stat.value}</span>
              </div>
              <span className="text-sm text-muted-foreground">{stat.label}</span>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
});
