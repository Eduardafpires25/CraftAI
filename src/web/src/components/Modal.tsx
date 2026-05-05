import { X } from "lucide-react";
import { ReactNode, useEffect } from "react";

interface Props {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  maxWidth?: string;
}

export function Modal({ open, onClose, title, children, maxWidth = "max-w-lg" }: Props) {
  useEffect(() => {
    if (!open) return;
    const onEsc = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onEsc);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onEsc);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center px-4 py-8"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      <div
        className={`relative card p-6 w-full ${maxWidth} max-h-full overflow-auto shadow-2xl`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-4">
          {title && <h2 className="text-xl font-bold">{title}</h2>}
          <button
            onClick={onClose}
            aria-label="Fechar"
            className="ml-auto p-1.5 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-ink-700/60"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
