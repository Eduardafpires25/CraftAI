import { useState, useEffect } from "react";
import { api } from "../lib/api";

export interface CartItem {
  id: string;
  user_id: string;
  seller_id: string;
  product_spec_id: string | null;
  order_id: string | null;
  selected_options: string | null;
  quantity: number;
  unit_price: number;
  total_price: number;
  name: string;
  description: string | null;
  image_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface Cart {
  items: CartItem[];
  total: number;
  total_items: number;
  grouped_by_seller: Record<string, CartItem[]>;
}

export function useCart() {
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCart = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<Cart>("/cart/");
      console.log("Carrinho atualizado:", response.data);
      setCart(response.data);
    } catch (err: any) {
      console.error("Erro ao carregar carrinho:", err);
      setError(err.response?.data?.detail || "Erro ao carregar carrinho");
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (data: {
    product_spec_id?: string;
    order_id?: string;
    quantity?: number;
    selected_options?: string;
  }) => {
    setLoading(true);
    setError(null);
    try {
      await api.post<CartItem>("/cart/items", data);
      await fetchCart();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erro ao adicionar ao carrinho");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateQuantity = async (itemId: string, quantity: number) => {
    setLoading(true);
    setError(null);
    try {
      await api.patch<CartItem>(`/cart/items/${itemId}`, { quantity });
      await fetchCart();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erro ao atualizar quantidade");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const removeItem = async (itemId: string) => {
    setLoading(true);
    setError(null);
    try {
      await api.delete(`/cart/items/${itemId}`);
      await fetchCart();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erro ao remover item");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const checkout = async (sellerIds: string[], ignoreErrors = false, shippingInfo?: {
    shipping_address: string;
    shipping_number?: string;
    shipping_complement?: string;
    shipping_city: string;
    shipping_state: string;
    shipping_zip_code: string;
    shipping_phone: string;
  }) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post<{ order_ids: string[]; total_amount: number; message: string }>("/cart/checkout", {
        seller_ids: sellerIds,
        ignore_errors: ignoreErrors,
        ...shippingInfo,
      });
      await fetchCart();
      return response.data;
    } catch (err: any) {
      console.error("Erro no checkout:", err);
      setError(err.response?.data?.detail || "Erro ao fazer checkout");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCart();
    // Atualiza o carrinho a cada 30 segundos para manter o contador atualizado
    const interval = setInterval(fetchCart, 20000);
    return () => clearInterval(interval);
  }, []);

  return {
    cart,
    loading,
    error,
    fetchCart,
    addToCart,
    updateQuantity,
    removeItem,
    checkout,
  };
}
