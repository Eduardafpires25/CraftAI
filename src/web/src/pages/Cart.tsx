import axios from "axios";
import { Loader2, Minus, Package, Plus, ShoppingBag, Trash2 } from "lucide-react";
import { useState } from "react";
import { api } from "../lib/api";
import { useCart } from "../hooks/useCart";
import { PhoneInput } from "../components/PhoneInput";
import { ProtectedRoute } from "../components/ProtectedRoute";
import { Toast } from "../components/Toast";

function CartItem({ item, updateQuantity, removeItem, loading }: { item: any; updateQuantity: (id: string, quantity: number) => Promise<void>; removeItem: (id: string) => Promise<void>; loading: boolean }) {
  const handleQuantityChange = async (newQuantity: number) => {
    if (newQuantity < 1) return;
    try {
      await updateQuantity(item.id, newQuantity);
    } catch (error) {
      console.error("Erro ao atualizar quantidade:", error);
    }
  };

  const handleRemove = async () => {
    try {
      await removeItem(item.id);
    } catch (error) {
      console.error("Erro ao remover item:", error);
    }
  };

  return (
    <div className="flex gap-4 p-4 bg-white dark:bg-ink-800 rounded-lg border border-slate-200 dark:border-ink-700">
      <div className="w-24 h-24 rounded-md overflow-hidden flex-shrink-0 bg-slate-100 dark:bg-ink-700/50 flex items-center justify-center">
        {item.image_url ? (
          <img
            src={item.image_url}
            alt={item.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <Package className="w-10 h-10 text-slate-300 dark:text-ink-600" />
        )}
      </div>
      <div className="flex-1">
        <h3 className="font-semibold text-slate-900 dark:text-white">{item.name}</h3>
        {item.description && (
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{item.description}</p>
        )}
        <p className="text-lg font-bold text-brand-500 mt-2">
          R$ {Number(item.unit_price).toFixed(2)}
        </p>
      </div>
      <div className="flex flex-col items-end gap-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleQuantityChange(item.quantity - 1)}
            disabled={loading || item.quantity <= 1}
            className="p-1 rounded hover:bg-slate-100 dark:hover:bg-ink-700 disabled:opacity-50"
          >
            <Minus className="w-4 h-4" />
          </button>
          <span className="w-8 text-center font-medium">{item.quantity}</span>
          <button
            onClick={() => handleQuantityChange(item.quantity + 1)}
            disabled={loading}
            className="p-1 rounded hover:bg-slate-100 dark:hover:bg-ink-700 disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        <button
          onClick={handleRemove}
          disabled={loading}
          className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 disabled:opacity-50"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

const BRAZILIAN_STATES = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
  "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
];

export default function CartPage() {
  const { cart, loading, checkout, updateQuantity, removeItem } = useCart();
  const [toast, setToast] = useState<{ show: boolean; message: string; type: "success" | "error" }>({ show: false, message: "", type: "success" });
  const [ignoreErrors, setIgnoreErrors] = useState(false);
  const [shippingAddress, setShippingAddress] = useState("");
  const [shippingNumber, setShippingNumber] = useState("");
  const [shippingComplement, setShippingComplement] = useState("");
  const [shippingCity, setShippingCity] = useState("");
  const [shippingState, setShippingState] = useState("");
  const [shippingZipCode, setShippingZipCode] = useState("");
  const [shippingPhone, setShippingPhone] = useState("");
  const [noNumber, setNoNumber] = useState(false);
  const [loadingCep, setLoadingCep] = useState(false);

  const fetchAddressByCep = async (cep: string) => {
    const cleanCep = cep.replace(/\D/g, "");
    if (cleanCep.length !== 8) return;

    setLoadingCep(true);
    try {
      const response = await fetch(`https://viacep.com.br/ws/${cleanCep}/json/`);
      const data = await response.json();
      
      if (data.erro) {
        setToast({ show: true, message: "CEP não encontrado.", type: "error" });
        return;
      }

      setShippingAddress(data.logradouro || "");
      setShippingCity(data.localidade || "");
      setShippingState(data.uf || "");
    } catch (error) {
      console.error("Erro ao buscar CEP:", error);
      setToast({ show: true, message: "Erro ao buscar CEP. Verifique sua conexão.", type: "error" });
    } finally {
      setLoadingCep(false);
    }
  };

  const handleCepChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const cleanValue = value.replace(/\D/g, "");
    let formatted = "";
    
    if (cleanValue.length > 0) {
      formatted = cleanValue.substring(0, 5);
      if (cleanValue.length > 5) {
        formatted += "-" + cleanValue.substring(5, 8);
      }
    }
    
    setShippingZipCode(formatted);
  };

  const handleCepKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!/[0-9]/.test(e.key) && !e.key.startsWith("Backspace") && !e.key.startsWith("Delete") && !e.key.startsWith("Arrow") && !e.key.startsWith("Tab")) {
      e.preventDefault();
    }
  };

  const handleCheckout = async () => {
    if (!cart || cart.items.length === 0) return;

    // Valida campos de endereço
    if (!shippingAddress || !shippingCity || !shippingState || !shippingZipCode || !shippingPhone) {
      setToast({ show: true, message: "Preencha todos os campos de endereço para entrega.", type: "error" });
      return;
    }

    if (!noNumber && !shippingNumber) {
      setToast({ show: true, message: "Informe o número ou marque 'Sem número'.", type: "error" });
      return;
    }

    const sellerIds = [...new Set(cart.items.map((item) => item.seller_id))];
    try {
      const result = await checkout(sellerIds, ignoreErrors, {
        shipping_address: shippingAddress,
        shipping_number: noNumber ? "S/N" : shippingNumber,
        shipping_complement: shippingComplement,
        shipping_city: shippingCity,
        shipping_state: shippingState,
        shipping_zip_code: shippingZipCode,
        shipping_phone: shippingPhone,
      });
      setToast({ show: true, message: `Checkout realizado! Total: R$ ${Number(result.total_amount).toFixed(2)}`, type: "success" });
    } catch (error) {
      console.error("Erro ao fazer checkout:", error);
      setToast({ show: true, message: "Erro ao fazer checkout. Tente novamente.", type: "error" });
    }
  };

  if (loading && !cart) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-200 dark:bg-ink-700 rounded mb-4"></div>
          <div className="h-32 bg-slate-200 dark:bg-ink-700 rounded mb-4"></div>
          <div className="h-32 bg-slate-200 dark:bg-ink-700 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <ProtectedRoute>
      <div className="max-w-4xl mx-auto p-6">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-6">Meu Carrinho</h1>

        {!cart || cart.items.length === 0 ? (
          <div className="text-center py-12">
            <ShoppingBag className="w-16 h-16 mx-auto text-slate-400 mb-4" />
            <h2 className="text-xl font-semibold text-slate-700 dark:text-slate-300 mb-2">
              Seu carrinho está vazio
            </h2>
            <p className="text-slate-600 dark:text-slate-400 mb-6">
              Adicione produtos para começar suas compras
            </p>
            <a
              href="/sellers"
              className="btn-primary inline-block"
            >
              Ver Produtos
            </a>
          </div>
        ) : (
          <>
            <div className="space-y-4 mb-6">
              {cart.items.map((item) => (
                <CartItem
                  key={item.id}
                  item={item}
                  updateQuantity={updateQuantity}
                  removeItem={removeItem}
                  loading={loading}
                />
              ))}
            </div>

            <div className="card p-6">
              <h3 className="font-semibold mb-4">Endereço de Entrega</h3>
              <div className="space-y-4 mb-6">
                <div>
                  <label className="label">Endereço</label>
                  <input
                    type="text"
                    value={shippingAddress}
                    onChange={(e) => setShippingAddress(e.target.value)}
                    className="input"
                    placeholder="Rua, Avenida, etc."
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Número</label>
                    <input
                      type="text"
                      value={shippingNumber}
                      onChange={(e) => setShippingNumber(e.target.value)}
                      className="input"
                      placeholder="123"
                      disabled={noNumber}
                    />
                  </div>
                  <div>
                    <label className="label">Complemento (opcional)</label>
                    <input
                      type="text"
                      value={shippingComplement}
                      onChange={(e) => setShippingComplement(e.target.value)}
                      className="input"
                      placeholder="Apto, Bloco, etc."
                    />
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="noNumber"
                    checked={noNumber}
                    onChange={(e) => {
                      setNoNumber(e.target.checked);
                      if (e.target.checked) {
                        setShippingNumber("S/N");
                      } else {
                        setShippingNumber("");
                      }
                    }}
                    className="w-4 h-4 accent-brand-500 cursor-pointer"
                  />
                  <label htmlFor="noNumber" className="text-sm cursor-pointer text-slate-600 dark:text-slate-400">Sem número</label>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Cidade</label>
                    <input
                      type="text"
                      value={shippingCity}
                      onChange={(e) => setShippingCity(e.target.value)}
                      className="input"
                      placeholder="Cidade"
                      required
                    />
                  </div>
                  <div>
                    <label className="label">UF</label>
                    <select
                      value={shippingState}
                      onChange={(e) => setShippingState(e.target.value)}
                      className="input"
                      required
                    >
                      <option value="">Selecione</option>
                      {BRAZILIAN_STATES.map((state) => (
                        <option key={state} value={state}>{state}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">CEP</label>
                    <div className="relative">
                      <input
                        type="text"
                        value={shippingZipCode}
                        onChange={handleCepChange}
                        onKeyPress={handleCepKeyPress}
                        onBlur={() => fetchAddressByCep(shippingZipCode)}
                        className="input pr-10"
                        placeholder="00000-000"
                        maxLength={9}
                        required
                      />
                      {loadingCep && (
                        <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-brand-500" />
                      )}
                    </div>
                  </div>
                  <div>
                    <label className="label">Telefone</label>
                    <PhoneInput
                      value={shippingPhone}
                      onChange={setShippingPhone}
                      required
                      className="w-full"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-between items-center mb-4">
                <span className="text-lg text-slate-700 dark:text-slate-300">
                  Total ({cart.total_items} {cart.total_items === 1 ? "item" : "itens"})
                </span>
                <span className="text-2xl font-bold text-brand-500">
                  R$ {Number(cart.total).toFixed(2)}
                </span>
              </div>
              
              <label className="flex items-center gap-2 mb-4 cursor-pointer">
                <input
                  type="checkbox"
                  checked={ignoreErrors}
                  onChange={(e) => setIgnoreErrors(e.target.checked)}
                  className="w-4 h-4 rounded border-slate-300 text-brand-500 focus:ring-brand-500"
                />
                <span className="text-sm text-slate-600 dark:text-slate-400">
                  Ignorar erros durante checkout (modo desenvolvimento)
                </span>
              </label>
              
              <button
                onClick={handleCheckout}
                disabled={loading}
                className="w-full btn-primary !py-3"
              >
                {loading ? "Processando..." : "Ir para o Pagamento"}
              </button>
            </div>
          </>
        )}

        <Toast
          show={toast.show}
          message={toast.message}
          type={toast.type}
          onClose={() => setToast({ show: false, message: "", type: "success" })}
        />
      </div>
    </ProtectedRoute>
  );
}
