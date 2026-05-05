import { createContext, useContext, useState, ReactNode, useEffect } from "react";
import { api } from "../lib/api";

interface IterationsContextType {
  iterationsLimit: { enabled: boolean; remaining: number } | null;
  fetchIterationsLimit: () => Promise<void>;
}

const IterationsContext = createContext<IterationsContextType | undefined>(undefined);

export function IterationsProvider({ children }: { children: ReactNode }) {
  const [iterationsLimit, setIterationsLimit] = useState<{ enabled: boolean; remaining: number } | null>(null);

  const fetchIterationsLimit = async () => {
    try {
      const response = await api.get("/users/me/iterations-limit");
      setIterationsLimit(response.data);
    } catch (error) {
      console.error("Erro ao buscar limite de iterações:", error);
    }
  };

  useEffect(() => {
    fetchIterationsLimit();
  }, []);

  return (
    <IterationsContext.Provider value={{ iterationsLimit, fetchIterationsLimit }}>
      {children}
    </IterationsContext.Provider>
  );
}

export function useIterations() {
  const context = useContext(IterationsContext);
  if (context === undefined) {
    throw new Error("useIterations must be used within an IterationsProvider");
  }
  return context;
}
