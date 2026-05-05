import axios from "axios";
import { Camera, Loader2, Save, User, Sparkles } from "lucide-react";
import { useRef, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useIterations } from "../contexts/IterationsContext";

export function UserProfilePage() {
  const { user, refresh } = useAuth();
  const { iterationsLimit } = useIterations();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.patch("/users/me", { name, email });
      await refresh();
      setEditing(false);
    } catch (e) {
      if (axios.isAxiosError(e)) setError(e.response?.data?.detail || "Falha ao salvar.");
      else setError("Erro inesperado.");
    } finally {
      setSaving(false);
    }
  };

  const handleAvatarUpload = async (file: File) => {
    setUploading(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      await api.post("/users/me/avatar", fd, { headers: { "Content-Type": "multipart/form-data" } });
      await refresh();
    } catch {
      setError("Falha no upload do avatar.");
    } finally {
      setUploading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-bold mb-6">Meu perfil</h1>

      <div className="card p-6">
        {/* Avatar */}
        <div className="flex items-start gap-6 mb-6">
          <div className="relative">
            <div className="w-24 h-24 rounded-2xl bg-slate-100 dark:bg-ink-700/50 overflow-hidden flex items-center justify-center">
              {user.avatar_url ? (
                <img src={user.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
              ) : (
                <User className="w-10 h-10 text-slate-400" />
              )}
            </div>
            <button
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
              className="absolute -bottom-1 -right-1 w-7 h-7 rounded-full bg-brand-500 text-white flex items-center justify-center hover:bg-brand-600 disabled:opacity-60"
              aria-label="Trocar avatar"
            >
              {uploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Camera className="w-3.5 h-3.5" />}
            </button>
            <input ref={fileRef} type="file" accept="image/*" hidden
              onChange={(e) => e.target.files?.[0] && handleAvatarUpload(e.target.files[0])} />
          </div>

          <div className="flex-1">
            <h2 className="text-xl font-semibold">{user.name || "Sem nome"}</h2>
            <p className="text-slate-500 dark:text-slate-400">{user.email}</p>
            <span className="inline-block mt-2 px-2 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-ink-700/60 text-slate-600 dark:text-slate-300 capitalize">
              {user.role === "client" ? "Cliente" : "Vendedor"}
            </span>
            {iterationsLimit && iterationsLimit.enabled && (
              <div className="mt-3 flex items-center gap-2 text-sm font-medium text-brand-600 dark:text-brand-400">
                <Sparkles className="w-4 h-4" />
                <span>{iterationsLimit.remaining} iterações restantes hoje</span>
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="mb-4 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/10 px-3 py-2 rounded-lg">
            {error}
          </div>
        )}

        {/* Form */}
        <div className="space-y-4">
          <div>
            <label className="label">Nome completo</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={!editing}
              className="input"
            />
          </div>

          <div>
            <label className="label">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={!editing}
              className="input"
            />
          </div>

          <div className="flex gap-2 pt-2">
            {editing ? (
              <>
                <button onClick={handleSave} disabled={saving} className="btn-primary disabled:opacity-60">
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  Salvar
                </button>
                <button onClick={() => { setEditing(false); setName(user.name ?? ""); setEmail(user.email); }} className="btn-outline">
                  Cancelar
                </button>
              </>
            ) : (
              <button onClick={() => setEditing(true)} className="btn-primary">
                Editar perfil
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
