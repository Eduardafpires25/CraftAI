import { Moon, Sun } from "lucide-react";
import { useTheme } from "../lib/theme";

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button
      onClick={toggle}
      aria-label={theme === "dark" ? "Mudar para tema claro" : "Mudar para tema escuro"}
      className="p-2 rounded-lg text-slate-600 hover:bg-slate-100
                 dark:text-slate-300 dark:hover:bg-ink-700/60 transition-colors"
    >
      {theme === "dark" ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
    </button>
  );
}
