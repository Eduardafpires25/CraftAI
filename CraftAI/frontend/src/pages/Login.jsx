import { useState } from 'react'
import { authAPI } from '../services/api'
import { Eye, EyeOff, LogIn } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'

function Login() {
  const [formData, setFormData] = useState({ email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const location = useLocation()
  const successMessage = location.state?.successMessage || ''

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const response = await authAPI.login(formData)
      localStorage.setItem('token', response.data.access_token)
      setSuccess('Login realizado com sucesso.')
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao fazer login')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-slate-100 mb-2">CraftAI</h1>
          <p className="text-slate-400">Acesso da aplicação</p>
        </div>

        <div className="card">
          <h2 className="text-2xl font-semibold text-slate-100 mb-6">Entrar</h2>

          {error && <div className="bg-red-900/20 border border-red-500 text-red-400 px-4 py-3 rounded-lg mb-4">{error}</div>}
          {(successMessage || success) && <div className="bg-green-900/20 border border-green-500 text-green-400 px-4 py-3 rounded-lg mb-4">{successMessage || success}</div>}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-100 mb-2">Email</label>
              <input type="email" name="email" value={formData.email} onChange={handleChange} className="input" placeholder="seu@email.com" required />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-100 mb-2">Senha</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className="input pr-10"
                  placeholder="********"
                  maxLength="72"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-100"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary w-full flex items-center justify-center gap-2">
              {loading ? <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div> : <><LogIn size={20} />Entrar</>}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-400">
              Não tem uma conta? <Link to="/register" className="text-blue-400 hover:text-blue-300">Cadastre-se</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
