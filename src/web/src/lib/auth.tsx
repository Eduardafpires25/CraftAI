import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from "react";
import { api } from "./api";
import type { LoginPayload, RegisterPayload, TokenResponse, User } from "../types/api";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<User>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

export function setTokens(t: TokenResponse) {
  localStorage.setItem(ACCESS_KEY, t.access_token);
  localStorage.setItem(REFRESH_KEY, t.refresh_token);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const { data } = await api.get<User>("/auth/me");
      setUser(data);
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  const login = async (payload: LoginPayload) => {
    const { data } = await api.post<TokenResponse>("/auth/login", payload);
    setTokens(data);
    await fetchMe();
  };

  const register = async (payload: RegisterPayload) => {
    const { data } = await api.post<User>("/auth/register", payload);
    return data;
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      // ignora
    }
    clearTokens();
    setUser(null);
  };

  const refresh = fetchMe;

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de AuthProvider");
  return ctx;
}
