import { ArrowRight, Loader2, Sparkles, Store } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { formatCategory } from "../types/api";
import type { SellerListResponse } from "../types/api";

export function ChatAIPage() {
  const [sellers, setSellers] = useState<SellerListResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<SellerListResponse>("/sellers/", { params: { limit: 6 } })
      .then(({ data }) => setSellers(data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <div className="text-center mb-10">
        <div className="inline-flex w-16 h-16 rounded-2xl bg-brand-500/10 items-center justify-center mb-4">
          <Sparkles className="w-8 h-8 text-brand-500" />
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight">
          Crie sua arte com <span className="text-brand-500">IA</span>
        </h1>
        <p className="text-slate-500 dark:text-slate-400 max-w-xl mx-auto mt-3">
          Escolha uma loja parceira, descreva sua ideia e nossa IA gerará prévias até a versão perfeita.
        </p>
      </div>

      <h2 className="text-lg font-semibold mb-4">Escolha uma loja para começar</h2>

      {loading ? (
        <div className="flex justify-center py-10"><Loader2 className="w-7 h-7 animate-spin text-brand-500" /></div>
      ) : !sellers?.items.length ? (
        <div className="card p-10 text-center text-slate-500">
          <Store className="w-10 h-10 mx-auto mb-2 text-slate-300 dark:text-ink-600" />
          Nenhuma loja disponível no momento.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {sellers.items.map((s) => (
            <Link
              key={s.id}
              to={`/sellers/${s.slug}`}
              className="card p-5 flex items-center gap-4 hover:-translate-y-0.5 transition-transform group"
            >
              <div className="w-14 h-14 rounded-xl bg-slate-100 dark:bg-ink-700/50 flex items-center justify-center overflow-hidden shrink-0">
                {s.logo_url ? (
                  <img src={s.logo_url} alt={s.store_name} className="w-full h-full object-cover" />
                ) : (
                  <Store className="w-6 h-6 text-slate-400" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold truncate">{s.store_name}</h3>
                <p className="text-xs text-brand-500">{formatCategory(s.category)}</p>
              </div>
              <ArrowRight className="w-5 h-5 text-slate-400 group-hover:text-brand-500 transition-colors" />
            </Link>
          ))}
        </div>
      )}

      <div className="mt-6 text-center">
        <Link to="/sellers" className="btn-outline">Ver todas as lojas</Link>
      </div>
    </div>
  );
}
