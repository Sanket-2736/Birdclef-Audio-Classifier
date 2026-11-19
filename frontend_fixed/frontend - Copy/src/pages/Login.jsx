import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const validateForm = () => {
    if (!email || !password) {
      setError('Email and password are required')
      return false
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Invalid email format')
      return false
    }
    return true
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!validateForm()) return

    setLoading(true)
    const result = await login(email, password)

    if (result.success) {
      navigate('/analyze')
    } else {
      setError(result.error || 'Login failed')
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#fff8e8] px-4 py-12 text-[#171717]">
      <div className="w-full max-w-md">
        <div className="bg-white border-2 border-black p-8 shadow-[8px_8px_0_#171717]">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 border-2 border-black bg-[#b9e7ff] px-3 py-1.5 shadow-[3px_3px_0_#171717] mb-6">
              <span className="h-2 w-2 rounded-full bg-[#171717]" />
              <span className="font-mono text-xs font-bold uppercase tracking-widest">WildEcho / Account Access</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2">
              BirdCLEF <span className="bg-[#f4c542] px-1">Classifier</span>
            </h1>
            <p className="text-[#625d53]">Sign in to your account</p>
          </div>

          {error && (
            <div className="bg-[#ffcfdb] border-2 border-black text-[#171717] px-4 py-3 mb-6 font-semibold text-sm shadow-[3px_3px_0_#171717]">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block font-mono text-xs font-bold uppercase tracking-wider mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-4 py-3 bg-[#fffdf7] border-2 border-black text-[#171717] placeholder-[#9a9387] focus:outline-none focus:ring-2 focus:ring-[#f4c542] focus:ring-offset-2 transition"
              />
            </div>

            <div>
              <label htmlFor="password" className="block font-mono text-xs font-bold uppercase tracking-wider mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-3 bg-[#fffdf7] border-2 border-black text-[#171717] placeholder-[#9a9387] focus:outline-none focus:ring-2 focus:ring-[#f4c542] focus:ring-offset-2 transition"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-[#f4c542] border-2 border-black shadow-[4px_4px_0_#171717] hover:shadow-[2px_2px_0_#171717] hover:translate-x-[2px] hover:translate-y-[2px] disabled:opacity-60 disabled:cursor-not-allowed font-extrabold uppercase tracking-wide transition duration-200"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-7 pt-6 border-t-2 border-dashed border-[#c9c1b2] text-center">
            <p className="text-[#625d53]">
              Don't have an account?{' '}
              <Link to="/register" className="font-extrabold text-[#171717] underline decoration-2 decoration-[#f4c542] underline-offset-4 hover:bg-[#f4c542] transition">
                Sign up
              </Link>
            </p>
          </div>
        </div>
        <p className="text-center mt-6 font-mono text-[10px] uppercase tracking-[0.2em] text-[#8a8378]">
          WildEcho · Bird Audio Intelligence
        </p>
      </div>
    </div>
  )
}
