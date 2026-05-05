import { Check, X, AlertCircle } from "lucide-react";
import { useEffect, useState } from "react";

type ToastType = "success" | "error";

interface ToastProps {
  message: string;
  show: boolean;
  onClose: () => void;
  duration?: number;
  type?: ToastType;
}

export function Toast({ message, show, onClose, duration = 3000, type = "success" }: ToastProps) {
  const [visible, setVisible] = useState(show);

  useEffect(() => {
    setVisible(show);
  }, [show]);

  useEffect(() => {
    if (visible && duration > 0) {
      const timer = setTimeout(() => {
        setVisible(false);
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [visible, duration, onClose]);

  if (!visible) return null;

  const bgColor = type === "success" ? "bg-green-500" : "bg-red-500";
  const hoverBgColor = type === "success" ? "hover:bg-green-600" : "hover:bg-red-600";
  const Icon = type === "success" ? Check : AlertCircle;

  return (
    <div className="fixed bottom-4 right-4 z-50 animate-in slide-in-from-right duration-300">
      <div className={`${bgColor} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 min-w-[300px]`}>
        <Icon className="w-5 h-5 flex-shrink-0" />
        <span className="flex-1 text-sm font-medium">{message}</span>
        <button
          onClick={() => {
            setVisible(false);
            onClose();
          }}
          className={`flex-shrink-0 ${hoverBgColor} rounded p-0.5 transition-colors`}
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
