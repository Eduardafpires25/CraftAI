import axios from "axios";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Logo } from "../components/Logo";
import { useAuth } from "../lib/auth";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login({ email, password });
      const from = (location.state as { from?: string })?.from || "/";
      navigate(from, { replace: true });
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || "Falha no login.");
      } else {
        setError("Erro inesperado.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        <div className="flex justify-center mb-8">
          <Logo size="lg" />
        </div>

        <div className="card p-8">
          <h1 className="text-2xl font-bold mb-1">Entrar</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
            Acesse sua conta para personalizar pedidos.
          </p>

          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="label">E-mail</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="voce@email.com"
              />
            </div>

            <div>
              <label className="label">Senha</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/10 px-3 py-2 rounded-lg">
                {error}
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-60">
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              Entrar
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
            Não tem conta?{" "}
            <Link to="/register" className="text-brand-500 hover:underline font-medium">
              Cadastre-se
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
