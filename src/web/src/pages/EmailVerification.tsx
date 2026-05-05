import axios from "axios";
import { Loader2, Mail, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Logo } from "../components/Logo";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

export function EmailVerificationPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    // Se email já verificado, redireciona
    if (user?.email_verified) {
      navigate("/", { replace: true });
    }
  }, [user, navigate]);

  const handleSendCode = async () => {
    setError(null);
    setSending(true);
    try {
      await api.post("/email/send-verification");
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(typeof err.response?.data?.detail === "string" ? err.response.data.detail : "Falha ao enviar código.");
      } else {
        setError("Erro inesperado.");
      }
    } finally {
      setSending(false);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.post("/email/verify", { code });
      // Recarrega o usuário para atualizar email_verified
      window.location.href = "/";
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(typeof err.response?.data?.detail === "string" ? err.response.data.detail : "Código inválido.");
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
          <div className="flex justify-center mb-4">
            <Mail className="w-12 h-12 text-brand-500" />
          </div>
          <h1 className="text-2xl font-bold mb-1 text-center">Verificar email</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-6 text-center">
            Enviamos um código para <span className="font-medium text-slate-700 dark:text-slate-300">{user?.email}</span>
          </p>

          <form onSubmit={handleVerify} className="space-y-4">
            <div>
              <label className="label">Código de verificação</label>
              <input
                required
                minLength={6}
                maxLength={10}
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                className="input text-center text-2xl tracking-widest"
                placeholder="000000"
                autoFocus
              />
            </div>

            {error && (
              <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/10 px-3 py-2 rounded-lg">
                {error}
              </div>
            )}

            {success && (
              <div className="text-sm text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-500/10 px-3 py-2 rounded-lg">
                Código enviado com sucesso!
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-60">
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              Verificar
            </button>
          </form>

          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={handleSendCode}
              disabled={sending}
              className="text-sm text-brand-500 hover:text-brand-600 disabled:opacity-60 inline-flex items-center gap-1"
            >
              {sending && <Loader2 className="w-3 h-3 animate-spin" />}
              <RefreshCw className="w-3 h-3" />
              Reenviar código
            </button>
          </div>

          <div className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
            <Link to="/" className="text-slate-500 hover:text-slate-700 dark:hover:text-slate-300">
              Voltar para home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
