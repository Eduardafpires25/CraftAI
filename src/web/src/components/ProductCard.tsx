import { ImageIcon, Sparkles } from "lucide-react";

interface Props {
  title: string;
  subtitle: string;
  price?: string;
  imageUrl?: string | null;
  ctaLabel?: string;
  highlight?: boolean;
  onClick?: () => void;
}

export function ProductCard({
  title,
  subtitle,
  price,
  imageUrl,
  ctaLabel = "Personalizar",
  highlight = false,
  onClick,
}: Props) {
  return (
    <div
      className={`card p-6 flex flex-col gap-4 transition-transform hover:-translate-y-1
                  ${highlight ? "ring-1 ring-brand-500/40 bg-gradient-to-br from-brand-500/10 to-transparent" : ""}`}
    >
      <div>
        <h3 className="font-semibold text-base">{title}</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 leading-snug mt-1">
          {subtitle}
        </p>
      </div>

      <div className="aspect-square w-full rounded-xl overflow-hidden bg-slate-100 dark:bg-ink-700/50 flex items-center justify-center">
        {imageUrl ? (
          <img src={imageUrl} alt={title} className="w-full h-full object-cover" />
        ) : (
          <ImageIcon className="w-12 h-12 text-slate-300 dark:text-ink-600" />
        )}
      </div>

      <div className="flex items-center justify-between mt-auto">
        {price && <div className="font-bold text-brand-500">{price}</div>}
        <button
          onClick={onClick}
          className="ml-auto inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-sm font-medium
                     bg-brand-500 hover:bg-brand-600 text-white transition-colors"
        >
          {highlight ? <Sparkles className="w-4 h-4" /> : null}
          {ctaLabel}
        </button>
      </div>
    </div>
  );
}
