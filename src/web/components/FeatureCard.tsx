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
      transition={{ duration: 0.4, delay }}
      className="group glass rounded-3xl p-7 hover:bg-card/80 transition-colors duration-300"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className={cn(
          "w-14 h-14 rounded-2xl flex items-center justify-center transition-transform duration-300 group-hover:scale-110",
          categoryBgColors[category]
        )}>
          <Icon className={cn("w-7 h-7", categoryColors[category])} />
        </div>
      </div>
      
      <h3 className="text-xl font-bold mb-5 text-foreground">
        {title}
      </h3>
      
      <ul className="space-y-3">
        {features.map((feature, index) => (
          <li
            key={index}
            className="flex items-start gap-3 text-sm text-muted-foreground"
          >
            <div className={cn(
              "w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5",
              categoryBgColors[category]
            )}>
              <Check className={cn("w-3 h-3", categoryColors[category])} />
            </div>
            <span>{feature}</span>
          </li>
        ))}
      </ul>
    </motion.div>
  );
});
