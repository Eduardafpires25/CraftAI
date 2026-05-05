import axios from "axios";
import {
  ArrowLeft, Check, CheckCircle2, Loader2, Package, Send, Sparkles, ShoppingCart, X, XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useIterations } from "../contexts/IterationsContext";
import { Modal } from "../components/Modal";
import { Toast } from "../components/Toast";
import { useCart } from "../hooks/useCart";
import type { Iteration, Order, OrderStatus } from "../types/api";

const statusLabels: Record<OrderStatus, string> = {
  draft: "Rascunho",
  in_analysis: "Em análise pelo seller",
  approved: "Aceito - aguardando pagamento",
  paid: "Pago - aguardando produção",
  in_production: "Em produção",
  sent: "Enviado",
  delivered: "Entregue",
  completed: "Concluído",
  cancelled: "Cancelado",
};

const statusBadge: Record<OrderStatus, string> = {
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

export function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const { iterationsLimit, fetchIterationsLimit } = useIterations();
  const navigate = useNavigate();
  const { addToCart } = useCart();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [description, setDescription] = useState("");
  const [generating, setGenerating] = useState(false);
  const [acting, setActing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [acceptPrice, setAcceptPrice] = useState("");
  const [showAcceptModal, setShowAcceptModal] = useState(false);
  const [showLimitModal, setShowLimitModal] = useState(false);
  const [toast, setToast] = useState<{ show: boolean; message: string; type: "success" | "error" }>({ show: false, message: "", type: "success" });

  const fetchOrder = async () => {
    if (!id) return;
    try {
      const { data } = await api.get<Order>(`/orders/${id}`);
      setOrder(data);
    } catch {
      setError("Pedido não encontrado.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchOrder(); /* eslint-disable-next-line */ }, [id]);

  const isClient = user?.id === order?.client_id;
  const isSeller = user?.id === order?.seller_id;
  const canIterate = isClient && order?.status === "draft";
  const canSubmit = isClient && order?.status === "draft" && order?.approved_iteration_id;
  const canCancelClient = isClient && (order?.status === "draft" || order?.status === "in_analysis");
  const canSellerDecide = isSeller && order?.status === "in_analysis";
  const canSellerProgress = isSeller && (order?.status === "paid" || order?.status === "in_production" || order?.status === "sent");

  const handleAction = async (fn: () => Promise<unknown>) => {
    setActing(true);
    setActionError(null);
    try {
      await fn();
      await fetchOrder();
    } catch (e) {
      if (axios.isAxiosError(e)) setActionError(e.response?.data?.detail || "Falha na operação.");
      else setActionError("Erro inesperado.");
    } finally {
      setActing(false);
    }
  };

  const generateIteration = async () => {
    if (!description.trim() || generating) return;
    setGenerating(true);
    setActionError(null);
    try {
      await api.post(`/orders/${id}/iterations`, { description });
      setDescription("");
      await fetchOrder();
      // Atualizar iterações restantes
      await fetchIterationsLimit();
    } catch (e) {
      if (axios.isAxiosError(e)) {
        const status = e.response?.status;
        // Tratar especificamente o erro de limite excedido (429)
        if (status === 429) {
          setShowLimitModal(true);
        } else {
          const detail = e.response?.data?.detail;
          setActionError(detail || "Falha na geração da imagem. Tente novamente mais tarde.");
        }
      } else {
        setActionError("Erro inesperado. Tente novamente.");
      }
    } finally {
      setGenerating(false);
    }
  };

  const approveIteration = (iterId: string) =>
    handleAction(() => api.post(`/orders/${id}/approve-iteration/${iterId}`));

  const submitOrder = () => handleAction(() => api.post(`/orders/${id}/submit`));

  const cancelOrder = () =>
    handleAction(() => api.post(`/orders/${id}/cancel`, { note: "Cancelado pelo cliente" }));

  const sellerAccept = () => setShowAcceptModal(true);
  const sellerReject = () =>
    handleAction(() => api.post(`/orders/${id}/seller-decision`, { accept: false, note: "Rejeitado" }));
  const updateStatus = (status: OrderStatus) =>
    handleAction(() => api.patch(`/orders/${id}/status`, { status }));

  const confirmDelivery = () =>
    handleAction(() => api.patch(`/orders/${id}/confirm-delivery`));

  const completeOrder = () =>
    handleAction(() => api.patch(`/orders/${id}/complete`));

  const confirmAcceptWithPrice = async () => {
    const price = parseFloat(acceptPrice);
    if (isNaN(price) || price <= 0) {
      setActionError("Digite um preço válido.");
      return;
    }
    await handleAction(() => api.post(`/orders/${id}/seller-decision`, { accept: true, estimated_price: price }));
    setShowAcceptModal(false);
    setAcceptPrice("");
  };

  const handleAddOrderToCart = async () => {
    if (!order) return;
    try {
      await addToCart({
        order_id: order.id,
        quantity: order.quantity,
      });
      setToast({ show: true, message: "Pedido adicionado ao carrinho! Vá para o carrinho para finalizar o pagamento.", type: "success" });
    } catch (error) {
      console.error("Erro ao adicionar pedido ao carrinho:", error);
      setToast({ show: true, message: "Erro ao adicionar pedido ao carrinho. Tente novamente.", type: "error" });
    }
  };

  if (loading) {
    return <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-brand-500" /></div>;
  }

  if (error || !order) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-20 text-center">
        <p className="text-slate-500">{error}</p>
        <button onClick={() => {
          if (user?.role === "seller") {
            navigate("/seller-dashboard");
          } else {
            navigate("/orders");
          }
        }} className="btn-outline mt-6">Voltar</button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <Link to={isSeller ? "/seller-dashboard" : "/orders"} className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-brand-500 mb-4">
        <ArrowLeft className="w-4 h-4" /> Voltar
      </Link>

      {/* Header do pedido */}
      <div className="card p-6 mb-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold">{order.title}</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">
              {order.product_type ?? "—"} • Qtd: {order.quantity}
              {order.estimated_price && <> • <span className="text-brand-500 font-semibold">R$ {order.estimated_price}</span></>}
            </p>
            <p className="text-sm text-slate-600 dark:text-slate-300 mt-3 max-w-2xl">{order.description}</p>
          </div>
          <span className={`px-3 py-1.5 rounded-full text-xs font-medium ${statusBadge[order.status]}`}>
            {statusLabels[order.status]}
          </span>
        </div>

        {actionError && (
          <div className="mt-4 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/10 px-3 py-2 rounded-lg">
            {actionError}
          </div>
        )}

        {/* Informações de envio */}
        {(order.shipping_address || order.shipping_city || order.shipping_state || order.shipping_zip_code || order.shipping_phone) && (
          <div className="mt-4 p-4 bg-slate-50 dark:bg-ink-700/30 rounded-lg">
            <h3 className="font-semibold text-sm mb-2 flex items-center gap-2">
              <Package className="w-4 h-4" /> Informações de envio
            </h3>
            <div className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
              {order.shipping_address && (
                <p>
                  {order.shipping_address}
                  {order.shipping_number && order.shipping_address && !order.shipping_address.includes(order.shipping_number) && `, ${order.shipping_number}`}
                  {order.shipping_complement && `, ${order.shipping_complement}`}
                </p>
              )}
              {(order.shipping_city || order.shipping_state || order.shipping_zip_code) && (
                <p>
                  {order.shipping_city && order.shipping_city}
                  {order.shipping_city && (order.shipping_state || order.shipping_zip_code) && ", "}
                  {order.shipping_state && order.shipping_state}
                  {order.shipping_state && order.shipping_zip_code && " - "}
                  {order.shipping_zip_code && order.shipping_zip_code}
                </p>
              )}
              {order.shipping_phone && <p>Telefone: {order.shipping_phone}</p>}
            </div>
          </div>
        )}

        {/* Acoes */}
        <div className="flex flex-wrap gap-2 mt-5">
          {canSubmit && (
            <button onClick={submitOrder} disabled={acting} className="btn-primary disabled:opacity-60">
              {acting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Enviar ao seller
            </button>
          )}
          {canCancelClient && (
            <button onClick={cancelOrder} disabled={acting}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-red-200 dark:border-red-500/30 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 disabled:opacity-60">
              <XCircle className="w-4 h-4" /> Cancelar pedido
            </button>
          )}
          {isClient && order.status === "approved" && order.estimated_price && (
            <button onClick={handleAddOrderToCart} disabled={acting} className="btn-primary disabled:opacity-60">
              <ShoppingCart className="w-4 h-4" /> Adicionar ao carrinho e pagar
            </button>
          )}
          {canSellerDecide && (
            <>
              <button onClick={sellerAccept} disabled={acting} className="btn-primary disabled:opacity-60">
                <Check className="w-4 h-4" /> Aceitar pedido
              </button>
              <button onClick={sellerReject} disabled={acting}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-red-200 dark:border-red-500/30 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 disabled:opacity-60">
                <X className="w-4 h-4" /> Rejeitar
              </button>
            </>
          )}
          {canSellerProgress && order.status === "approved" && (
            <button onClick={() => updateStatus("in_production")} disabled={acting} className="btn-primary disabled:opacity-60">
              <Package className="w-4 h-4" /> Iniciar produção
            </button>
          )}
          {canSellerProgress && order.status === "paid" && (
            <button onClick={() => updateStatus("in_production")} disabled={acting} className="btn-primary disabled:opacity-60">
              <Package className="w-4 h-4" /> Iniciar produção
            </button>
          )}
          {canSellerProgress && order.status === "in_production" && (
            <button onClick={() => updateStatus("sent")} disabled={acting} className="btn-primary disabled:opacity-60">
              <Package className="w-4 h-4" /> Marcar como enviado
            </button>
          )}
          {isClient && order.status === "sent" && (
            <button onClick={confirmDelivery} disabled={acting} className="btn-primary disabled:opacity-60">
              <Check className="w-4 h-4" /> Confirmar recebimento
            </button>
          )}
          {isClient && order.status === "delivered" && (
            <button onClick={completeOrder} disabled={acting} className="btn-primary disabled:opacity-60">
              <CheckCircle2 className="w-4 h-4" /> Marcar como concluído
            </button>
          )}
        </div>
      </div>

      {/* Iteracoes - apenas para pedidos personalizados */}
      {order.product_type === "customized" ? (
        <div className="mb-6">
          <div className="flex items-baseline justify-between mb-4">
            <h2 className="text-xl font-bold">Iterações</h2>
            <span className="text-sm text-slate-500">
              {order.iterations.length} {order.iterations.length === 1 ? "versão" : "versões"}
            </span>
          </div>

          {order.iterations.length === 0 ? (
            <div className="card p-10 text-center text-slate-500">
              <Sparkles className="w-10 h-10 mx-auto mb-2 text-brand-500/50" />
              <p>Nenhuma iteração ainda. Descreva sua ideia abaixo para gerar a primeira.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {order.iterations.map((it) => (
                <IterationCard
                  key={it.id}
                  iteration={it}
                  isApproved={order.approved_iteration_id === it.id}
                  canApprove={canIterate || false}
                  onApprove={() => approveIteration(it.id)}
                  disabled={acting}
                />
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Imagem do produto para pedidos regulares */
        <div className="mb-6">
          <h2 className="text-xl font-bold mb-4">Imagem do Produto</h2>
          <div className="card p-4">
            {order.image_url ? (
              <img
                src={order.image_url}
                alt={order.title}
                className="w-full max-w-md mx-auto rounded-lg object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                  (e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden');
                }}
              />
            ) : null}
            {(!order.image_url || order.image_url === '/placeholder-product.png') && (
              <div className="w-full max-w-md mx-auto rounded-lg bg-slate-100 dark:bg-ink-700/60 flex items-center justify-center aspect-square">
                <Package className="w-24 h-24 text-slate-300 dark:text-slate-600" />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Form de nova iteracao - apenas para pedidos personalizados */}
      {canIterate && order.product_type === "customized" && (
        <div className="card p-6">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-brand-500" />
            Nova iteração com IA
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
            Refine sua ideia. A cada nova descrição, a IA gera uma nova versão.
          </p>
          {iterationsLimit && iterationsLimit.enabled && (
            <div className="mb-4 flex items-center gap-2 text-sm font-medium text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-500/10 px-3 py-2 rounded-lg">
              <Sparkles className="w-4 h-4" />
              <span>{iterationsLimit.remaining} iterações restantes hoje</span>
            </div>
          )}
          <textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="input resize-none"
            placeholder="Ex.: Estilo aquarela, cores pasteis, fundo branco..."
          />
          <button
            onClick={generateIteration}
            disabled={generating || description.trim().length < 5}
            className="btn-primary mt-3 disabled:opacity-60"
          >
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Gerar nova versão
          </button>
        </div>
      )}

      <Modal open={showAcceptModal} onClose={() => { setShowAcceptModal(false); setAcceptPrice(""); }} title="Definir preço do pedido">
        <div className="space-y-4">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Defina o preço para este pedido. O cliente será notificado e poderá prosseguir com o pagamento.
          </p>
          <div>
            <label className="label">Preço (R$)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={acceptPrice}
              onChange={(e) => setAcceptPrice(e.target.value)}
              className="input"
              placeholder="29.90"
            />
          </div>
          {actionError && (
            <div className="text-sm text-red-600 dark:text-red-400">{actionError}</div>
          )}
          <button
            onClick={confirmAcceptWithPrice}
            disabled={acting || !acceptPrice}
            className="btn-primary w-full disabled:opacity-60"
          >
            {acting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
            Aceitar e definir preço
          </button>
        </div>
      </Modal>
      <Toast
        show={toast.show}
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ show: false, message: "", type: "success" })}
      />

      <Modal
        open={showLimitModal}
        onClose={() => setShowLimitModal(false)}
        title="Limite de iterações atingido"
        maxWidth="max-w-md"
      >
        <div className="space-y-4">
          <div className="flex items-center gap-3 text-amber-600 dark:text-amber-400">
            <Sparkles className="w-6 h-6" />
            <p className="font-semibold">Você atingiu o limite diário</p>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Você atingiu o limite de iterações com IA por dia. O limite é reiniciado diariamente às 00:00 UTC.
          </p>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Tente novamente amanhã para criar novas iterações.
          </p>
          <button
            onClick={() => setShowLimitModal(false)}
            className="btn-primary w-full"
          >
            Entendi
          </button>
        </div>
      </Modal>
    </div>
  );
}

function IterationCard({
  iteration, isApproved, canApprove, onApprove, disabled,
}: {
  iteration: Iteration;
  isApproved: boolean;
  canApprove: boolean;
  onApprove: () => void;
  disabled: boolean;
}) {
  return (
    <div className={`card p-4 flex flex-col gap-3 transition-all ${isApproved ? "ring-2 ring-brand-500" : ""}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-slate-500 dark:text-slate-400">v{iteration.version}</span>
        {isApproved && (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-brand-500">
            <CheckCircle2 className="w-3.5 h-3.5" /> Aprovada
          </span>
        )}
      </div>

      <div className="aspect-square w-full rounded-xl overflow-hidden bg-slate-100 dark:bg-ink-700/50 flex items-center justify-center">
        {iteration.status === "ready" || iteration.status === "approved" ? (
          iteration.image_url ? (
            <img src={iteration.image_url} alt={`v${iteration.version}`} className="w-full h-full object-cover" />
          ) : (
            <Sparkles className="w-10 h-10 text-slate-300" />
          )
        ) : iteration.status === "generating" || iteration.status === "pending" ? (
          <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
        ) : (
          <XCircle className="w-10 h-10 text-red-400" />
        )}
      </div>

      <p className="text-sm text-slate-600 dark:text-slate-300 line-clamp-3">{iteration.description}</p>

      {canApprove && !isApproved && (iteration.status === "ready" || iteration.status === "approved") && (
        <button
          onClick={onApprove}
          disabled={disabled}
          className="btn-outline w-full text-sm disabled:opacity-60"
        >
          <Check className="w-4 h-4" /> Escolher esta
        </button>
      )}
      {iteration.status === "failed" && (
        <p className="text-xs text-red-500">Falha na geração da imagem</p>
      )}
    </div>
  );
}
