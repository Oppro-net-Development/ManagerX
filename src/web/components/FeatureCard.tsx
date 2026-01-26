import { memo } from "react";
import { motion } from "framer-motion";
import { LucideIcon, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  features: string[];
  category: "moderation" | "community" | "social" | "interactive";
  delay?: number;
}

const categoryColors = {
  moderation: "text-red-400",
  community: "text-purple-400",
  social: "text-blue-400",
  interactive: "text-yellow-400",
};

const categoryBgColors = {
  moderation: "bg-red-500/10",
  community: "bg-purple-500/10",
  social: "bg-blue-500/10",
  interactive: "bg-yellow-500/10",
};

export const FeatureCard = memo(function FeatureCard({ 
  icon: Icon, 
  title, 
  features, 
  category, 
  delay = 0 
}: FeatureCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.6, delay, ease: "easeInOut" }}
      whileHover={{ y: -8, boxShadow: "0 20px 40px rgba(var(--primary), 0.15)" }}
      className="group glass rounded-3xl p-8 hover:bg-card/80 transition-all duration-500 ease-out border border-white/10 backdrop-blur-lg"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <motion.div 
          whileHover={{ scale: 1.1, rotate: 5 }}
          className={cn(
            "w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-300 shadow-lg",
            categoryBgColors[category]
          )}
        >
          <Icon className={cn("w-8 h-8", categoryColors[category])} />
        </motion.div>
      </div>
      
      <motion.h3 
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        transition={{ delay: delay + 0.2 }}
        className="text-2xl font-bold mb-6 text-foreground group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-primary group-hover:to-accent transition-all"
      >
        {title}
      </motion.h3>
      
      <div className="space-y-4">
        {features.map((feature, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -10 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: delay + 0.1 + index * 0.05 }}
            className="flex items-start gap-4 text-sm text-muted-foreground group-hover:text-foreground transition-colors"
          >
            <motion.div 
              whileHover={{ scale: 1.2 }}
              className={cn(
                "w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-1 shadow-md",
                categoryBgColors[category]
              )}
            >
              <Check className={cn("w-3.5 h-3.5", categoryColors[category])} />
            </motion.div>
            <span className="leading-relaxed">{feature}</span>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
});
