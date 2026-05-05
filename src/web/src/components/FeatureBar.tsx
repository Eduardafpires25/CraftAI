import { Headphones, Lock, ShieldCheck, Truck } from "lucide-react";

const features = [
  { icon: ShieldCheck, title: "Alta qualidade", subtitle: "Impressão premium" },
  { icon: Truck, title: "Envio rápido", subtitle: "Para todo o Brasil" },
  { icon: Lock, title: "Compra segura", subtitle: "Seus dados protegidos" },
  { icon: Headphones, title: "Atendimento", subtitle: "Suporte humano" },
];

export function FeatureBar() {
  return (
    <div className="card grid grid-cols-2 md:grid-cols-4 divide-x divide-slate-200 dark:divide-ink-600/60">
      {features.map((f) => (
        <div key={f.title} className="flex items-center gap-3 px-6 py-5">
          <f.icon className="w-6 h-6 text-brand-500 shrink-0" />
          <div>
            <div className="text-sm font-semibold">{f.title}</div>
            <div className="text-xs text-slate-500 dark:text-slate-400">{f.subtitle}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
