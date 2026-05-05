import { ArrowLeft, Clock, Instagram, Loader2, MapPin, MessageCircle, Package, Sparkles, Store, ShoppingCart } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { CreateOrderModal } from "../components/CreateOrderModal";
import { Modal } from "../components/Modal";
import { Toast } from "../components/Toast";
import { Tooltip } from "../components/Tooltip";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useCart } from "../hooks/useCart";
import { formatCategory } from "../types/api";
import type { ProductListItem, SellerDetail } from "../types/api";

export function SellerDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { addToCart } = useCart();
  const [seller, setSeller] = useState<SellerDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<ProductListItem | undefined>();
  const [showWarningModal, setShowWarningModal] = useState(false);
  const [toast, setToast] = useState<{ show: boolean; message: string; type: "success" | "error" }>({ show: false, message: "", type: "success" });

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    api.get<SellerDetail>(`/sellers/by-slug/${slug}`)
      .then(({ data }) => setSeller(data))
      .catch(() => setError("Loja não encontrada."))
      .finally(() => setLoading(false));
  }, [slug]);

  const handleStartOrder = (product?: ProductListItem) => {
    if (!user) {
      navigate("/login", { state: { from: `/sellers/${slug}` } });
      return;
    }
    // Impede vendedor de fazer pedido para própria loja
    if (user.id === seller.user_id) {
      setShowWarningModal(true);
      return;
    }
    setSelectedProduct(product);
    setShowCreate(true);
  };

  const handleAddToCart = async (product: ProductListItem) => {
    if (!user) {
      navigate("/login", { state: { from: `/sellers/${slug}` } });
      return;
    }
    if (user.id === seller.user_id) {
      setShowWarningModal(true);
      return;
    }
    if (product.is_customizable) {
      // Produtos personalizáveis vão pelo fluxo de pedido
      handleStartOrder(product);
      return;
    }
    try {
      await addToCart({
        product_spec_id: product.id,
        quantity: 1,
      });
      setToast({ show: true, message: "Produto adicionado ao carrinho!", type: "success" });
    } catch (error) {
      console.error("Erro ao adicionar ao carrinho:", error);
      setToast({ show: true, message: "Erro ao adicionar ao carrinho. Tente novamente.", type: "error" });
    }
  };

  if (loading) {
    return <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-brand-500" /></div>;
  }

  if (error || !seller) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-20 text-center">
        <p className="text-slate-500">{error}</p>
        <Link to="/sellers" className="btn-outline mt-6 inline-flex">Voltar</Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <Link to="/sellers" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-brand-500 mb-4">
        <ArrowLeft className="w-4 h-4" /> Voltar
      </Link>

      {/* Banner + Avatar */}
      <div className="relative mb-6">
        <div className="h-48 md:h-64 rounded-2xl overflow-hidden bg-gradient-to-br from-brand-500 via-purple-600 to-pink-500">
          {seller.banner_url ? (
            <img src={seller.banner_url} alt="" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Store className="w-16 h-16 text-white/30" />
            </div>
          )}
        </div>
        <div className="absolute -bottom-12 left-6 w-24 h-24 rounded-2xl bg-white dark:bg-ink-800 border-4 border-white dark:border-ink-900 flex items-center justify-center overflow-hidden shadow-lg">
          {seller.logo_url ? (
            <img src={seller.logo_url} alt={seller.store_name} className="w-full h-full object-cover" />
          ) : (
            <Store className="w-10 h-10 text-slate-400" />
          )}
        </div>
      </div>

      {/* Info loja */}
      <div className="flex flex-wrap items-start gap-6 mb-10 pl-32">

        <div className="flex-1 min-w-0">
          <h1 className="text-3xl font-bold">{seller.store_name}</h1>
          <p className="text-brand-500 text-sm font-medium mt-0.5">{formatCategory(seller.category)}</p>
          {seller.description && (
            <p className="text-slate-600 dark:text-slate-300 mt-3 max-w-2xl">{seller.description}</p>
          )}
          <div className="flex flex-wrap gap-4 mt-4 text-sm text-slate-500 dark:text-slate-400">
            {seller.city && (
              <span className="inline-flex items-center gap-1.5"><MapPin className="w-4 h-4" /> {seller.city}{seller.state ? `/${seller.state}` : ""}</span>
            )}
            {seller.estimated_days && (
              <span className="inline-flex items-center gap-1.5"><Clock className="w-4 h-4" /> {seller.estimated_days} dias</span>
            )}
            {seller.whatsapp && (
              <a href={`https://wa.me/${seller.whatsapp.replace(/\D/g, "")}`} target="_blank" rel="noreferrer"
                className="inline-flex items-center gap-1.5 hover:text-brand-500">
                <MessageCircle className="w-4 h-4" /> {seller.whatsapp}
              </a>
            )}
            {seller.instagram && (
              <a href={`https://instagram.com/${seller.instagram.replace("@", "")}`} target="_blank" rel="noreferrer"
                className="inline-flex items-center gap-1.5 hover:text-brand-500">
                <Instagram className="w-4 h-4" /> {seller.instagram}
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Produtos */}
      <h2 className="text-xl font-bold mb-4">Produtos disponíveis</h2>
      {seller.products.length === 0 ? (
        <div className="card p-10 text-center text-slate-500">
          <Package className="w-10 h-10 mx-auto mb-2 text-slate-300 dark:text-ink-600" />
          Esta loja ainda não cadastrou produtos.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {seller.products
            .filter(p => !p.is_customizable || seller.accepts_custom_designs)
            .map((p) => (
            <div key={p.id} className="card p-5 flex flex-col gap-3">
              <div className="aspect-square w-full rounded-xl bg-slate-100 dark:bg-ink-700/50 overflow-hidden flex items-center justify-center">
                {p.cover_url ? (
                  <img src={p.cover_url} alt={p.name} className="w-full h-full object-cover" />
                ) : (
                  <Package className="w-10 h-10 text-slate-300 dark:text-ink-600" />
                )}
              </div>
              <div>
                <h3 className="font-semibold">{p.name}</h3>
                <div className="mt-1">
                  {p.is_customizable && (
                    <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-brand-100 dark:bg-brand-500/20 text-brand-600 dark:text-brand-400">
                      Personalizável
                    </span>
                  )}
                </div>
                {p.description && (
                  <Tooltip content={p.description}>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">{p.description}</p>
                  </Tooltip>
                )}
              </div>
              <div className="flex items-center justify-between mt-auto">
                {p.base_price && <span className="font-bold text-brand-500">R$ {p.base_price}</span>}
                {p.is_customizable ? (
                  <button onClick={() => handleStartOrder(p)} className="ml-auto inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium">
                    <Sparkles className="w-3.5 h-3.5" /> Personalizar
                  </button>
                ) : (
                  <button onClick={() => handleAddToCart(p)} className="ml-auto inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium">
                    <ShoppingCart className="w-3.5 h-3.5" /> Adicionar
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <CreateOrderModal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        sellerId={seller.user_id}
        sellerName={seller.store_name}
        product={selectedProduct}
      />

      <Modal open={showWarningModal} onClose={() => setShowWarningModal(false)} title="Aviso">
        <div className="space-y-4">
          <p className="text-slate-600 dark:text-slate-400">
            Você não pode fazer pedidos para a sua própria loja.
          </p>
          <button onClick={() => setShowWarningModal(false)} className="btn-primary w-full">
            Entendi
          </button>
        </div>
      </Modal>

      <Toast
        show={toast.show}
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ show: false, message: "", type: "success" })}
      />
    </div>
  );
}
