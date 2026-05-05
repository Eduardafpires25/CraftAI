import axios from "axios";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Logo } from "../components/Logo";
import { PhoneInput } from "../components/PhoneInput";
import { useAuth } from "../lib/auth";
import type { UserRole } from "../types/api";

export function RegisterPage() {
  const { register, login } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [role, setRole] = useState<UserRole>("client");
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setFieldErrors({});
    setLoading(true);
    try {
      await register({ name, email, password, phone: phone || undefined, role });
      // Login automático após registro
      await login({ email, password });
      // Redireciona para a página inicial
      navigate("/", { replace: true });
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data;
        if (data?.errors && Array.isArray(data.errors)) {
          const map: Record<string, string> = {};
          for (const e of data.errors) map[e.field] = e.message;
          setFieldErrors(map);
        }
        setError(typeof data?.detail === "string" ? data.detail : "Falha ao cadastrar.");
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
          <h1 className="text-2xl font-bold mb-1">Criar conta</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
            É rápido e gratuito.
          </p>

          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="label">Nome</label>
              <input
                required minLength={2}
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input"
                placeholder="Seu nome"
              />
              {fieldErrors.name && <p className="text-xs text-red-500 mt-1">{fieldErrors.name}</p>}
            </div>

            <div>
              <label className="label">E-mail</label>
              <input
                type="email" required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="voce@email.com"
              />
              {fieldErrors.email && <p className="text-xs text-red-500 mt-1">{fieldErrors.email}</p>}
            </div>

            <div>
              <label className="label">Telefone <span className="text-slate-400 font-normal">(opcional)</span></label>
              <PhoneInput
                value={phone}
                onChange={setPhone}
                className="w-full"
              />
            </div>

            <div>
              <label className="label">Senha</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  required minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="Mínimo 8 caracteres"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {fieldErrors.password && <p className="text-xs text-red-500 mt-1">{fieldErrors.password}</p>}
            </div>

            <div>
              <label className="label">Tipo de conta</label>
              <div className="grid grid-cols-2 gap-2">
                {(["client", "seller"] as UserRole[]).map((r) => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setRole(r)}
                    className={`px-4 py-2.5 rounded-xl border text-sm font-medium transition-colors
                      ${role === r
                        ? "border-brand-500 bg-brand-500/10 text-brand-500"
                        : "border-slate-300 dark:border-ink-600 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-ink-700/40"
                      }`}
                  >
                    {r === "client" ? "Cliente" : "Vendedor"}
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/10 px-3 py-2 rounded-lg">
                {error}
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-60">
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              Criar conta
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
            Já tem conta?{" "}
            <Link to="/login" className="text-brand-500 hover:underline font-medium">
              Entrar
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
