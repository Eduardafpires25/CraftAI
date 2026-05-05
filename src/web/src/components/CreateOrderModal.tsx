import axios from "axios";
import { Loader2, Sparkles } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import type { Order, ProductListItem } from "../types/api";
import { Modal } from "./Modal";

interface Props {
  open: boolean;
  onClose: () => void;
  sellerId: string;
  sellerName: string;
  product?: ProductListItem;
}

export function CreateOrderModal({ open, onClose, sellerId, sellerName, product }: Props) {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [selectedOptions, setSelectedOptions] = useState<Record<string, string>>({});
  const [quantity, setQuantity] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.post<Order>("/orders/", {
        seller_id: sellerId,
        title,
        description,
        product_type: product?.is_customizable ? "customized" : (product?.name || null),
        product_options: Object.keys(selectedOptions).length > 0 ? selectedOptions : undefined,
        quantity,
      });
      navigate(`/orders/${data.id}`);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 401) {
          navigate("/login", { state: { from: `/sellers` } });
          return;
        }
        setError(err.response?.data?.detail || "Falha ao criar pedido.");
      } else {
        setError("Erro inesperado.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleOptionChange = (optionKey: string, value: string) => {
    setSelectedOptions(prev => ({ ...prev, [optionKey]: value }));
  };

  return (
    <Modal open={open} onClose={onClose} title={`Novo pedido - ${sellerName}`}>
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="label">Título</label>
          <input
            required minLength={3}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="input"
            placeholder="Ex.: Caneca personalizada do meu gato"
          />
        </div>

        <div>
          <label className="label">Descrição inicial <span className="text-slate-400 font-normal">(comentário para a loja)</span></label>
          <textarea
            required minLength={5}
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="input resize-none"
            placeholder="Conte sua ideia. Você poderá refinar depois com a IA."
          />
        </div>

        {product?.is_customizable && product.customization_options && (
          <div className="space-y-3 p-4 bg-slate-50 dark:bg-ink-800/50 rounded-lg">
            <h4 className="font-medium text-sm">Opções de personalização</h4>
            {Object.entries(product.customization_options).map(([key, values]) => (
              <div key={key}>
                <label className="label text-xs capitalize">{key}</label>
                <select
                  required
                  value={selectedOptions[key] || ""}
                  onChange={(e) => handleOptionChange(key, e.target.value)}
                  className="input"
                >
                  <option value="">Selecione...</option>
                  {Array.isArray(values) ? values.map((v: string) => (
                    <option key={v} value={v}>{v}</option>
                  )) : null}
                </select>
              </div>
            ))}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="label">Quantidade</label>
            <input
              type="number" min={1} max={10000}
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
              className="input"
            />
          </div>
        </div>

        {error && (
          <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/10 px-3 py-2 rounded-lg">
            {error}
          </div>
        )}

        <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-60">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          Criar e iterar com IA
        </button>
      </form>
    </Modal>
  );
}
