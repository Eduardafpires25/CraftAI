import { Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

interface Props {
  size?: "sm" | "md" | "lg";
  asLink?: boolean;
}

export function Logo({ size = "md", asLink = true }: Props) {
  const sizes = {
    sm: { icon: "w-5 h-5", text: "text-lg" },
    md: { icon: "w-7 h-7", text: "text-xl" },
    lg: { icon: "w-10 h-10", text: "text-3xl" },
  };
  const s = sizes[size];

  const inner = (
    <div className="flex items-center gap-2">
      <Sparkles className={`${s.icon} text-brand-500`} fill="currentColor" />
      <span className={`${s.text} font-extrabold tracking-tight`}>
        <span className="text-slate-900 dark:text-white">CRAFT</span>
        <span className="text-brand-500">AI</span>
      </span>
    </div>
  );

  return asLink ? <Link to="/">{inner}</Link> : inner;
}
