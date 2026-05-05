import { Loader2, Package } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { OrderListResponse, OrderStatus } from "../types/api";

const statusLabels: Record<OrderStatus, string> = {
  draft: "Rascunho",
  in_analysis: "Em análise",
  approved: "Aprovado",
  paid: "Pago",
  in_production: "Em produção",
  sent: "Enviado",
  delivered: "Entregue",
  completed: "Concluído",
  cancelled: "Cancelado",
};

const statusColors: Record<OrderStatus, string> = {
  draft: "bg-slate-100 text-slate-700 dark:bg-ink-700/60 dark:text-slate-300",
  in_analysis: "bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300",
  approved: "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300",
  paid: "bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-300",
  in_production: "bg-purple-100 text-purple-700 dark:bg-brand-500/20 dark:text-brand-300",
  sent: "bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-300",
  delivered: "bg-teal-100 text-teal-700 dark:bg-teal-500/20 dark:text-teal-300",
  completed: "bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-300",
  cancelled: "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300",
};

export function MyOrdersPage() {
  const [data, setData] = useState<OrderListResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<OrderListResponse>("/orders/me")
      .then(({ data }) => setData(data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <h1 className="text-3xl font-bold mb-2">Meus pedidos</h1>
      <p className="text-slate-500 dark:text-slate-400 mb-8">
        Acompanhe todos os seus pedidos, personalizados e regulares.
      </p>

      {data?.items.length ? (
        <div className="space-y-3">
          {data.items.map((o) => (
            <Link
              key={o.id}
              to={`/orders/${o.id}`}
              className="card p-5 flex items-center gap-4 hover:-translate-y-0.5 transition-transform"
            >
              <div className="w-16 h-16 rounded-xl bg-slate-100 dark:bg-ink-700/50 flex items-center justify-center overflow-hidden shrink-0">
                {o.cover_url ? (
                  <img src={o.cover_url} alt={o.title} className="w-full h-full object-cover" />
                ) : (
                  <Package className="w-7 h-7 text-slate-400" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold truncate">{o.title}</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {o.product_type ?? "—"} • Qtd: {o.quantity}
                </p>
              </div>
              <span
                className={`px-3 py-1 rounded-full text-xs font-medium ${statusColors[o.status]}`}
              >
                {statusLabels[o.status]}
              </span>
            </Link>
          ))}
        </div>
      ) : (
        <div className="card p-10 text-center text-slate-500">
          <Package className="w-12 h-12 mx-auto mb-3 text-slate-300 dark:text-ink-600" />
          <p>Você ainda não tem pedidos.</p>
          <Link to="/sellers" className="btn-primary mt-4">
            Explorar lojas
          </Link>
        </div>
      )}
    </div>
  );
}
