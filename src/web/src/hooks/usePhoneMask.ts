import { useState } from "react";

/**
 * Hook para máscara de telefone brasileiro
 * Formato: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX
 */
export function usePhoneMask(initialValue: string = "") {
  const [phone, setPhone] = useState(initialValue);

  const formatPhone = (value: string): string => {
    // Remove todos os caracteres não numéricos
    const numbers = value.replace(/\D/g, "");

    // Limita a 11 dígitos
    if (numbers.length > 11) {
      return phone;
    }

    // Aplica a máscara
    if (numbers.length === 0) {
      return "";
    } else if (numbers.length <= 2) {
      return `(${numbers}`;
    } else if (numbers.length <= 7) {
      return `(${numbers.slice(0, 2)}) ${numbers.slice(2)}`;
    } else if (numbers.length <= 11) {
      return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 7)}-${numbers.slice(7)}`;
    }

    return numbers;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhone(e.target.value);
    setPhone(formatted);
  };

  const getRawValue = (): string => {
    return phone.replace(/\D/g, "");
  };

  const isValid = (): boolean => {
    const numbers = phone.replace(/\D/g, "");
    // Valida telefone brasileiro: 10 ou 11 dígitos
    return numbers.length === 10 || numbers.length === 11;
  };

  return {
    phone,
    setPhone,
    handleChange,
    getRawValue,
    isValid,
  };
}
