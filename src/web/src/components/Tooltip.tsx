import { useState } from "react";

interface TooltipProps {
  content: string;
  children: React.ReactNode;
}

export function Tooltip({ content, children }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div
      className="relative inline-block group"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 z-50 px-3 py-2 text-sm rounded-lg shadow-lg max-w-xs bg-slate-200 text-slate-900 dark:bg-slate-800 dark:text-white whitespace-normal break-words">
          {content}
        </div>
      )}
    </div>
  );
}
