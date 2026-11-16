import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const validateForm = () => {
    const newErrors = {}

    if (!name.trim()) {
      newErrors.name = 'Name is required'
    }

    if (!email) {
      newErrors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Invalid email format'
    }

    if (!password) {
      newErrors.password = 'Password is required'
    } else if (password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters'
    }

    if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!validateForm()) return

    setLoading(true)
    const result = await register(name, email, password)

    if (result.success) {
      navigate('/analyze')
    } else {
      setErrors({ submit: result.error || 'Registration failed' })
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#fff8e8] px-4 py-10 text-[#171717]">
      <div className="w-full max-w-md">
        <div className="bg-white border-2 border-black p-8 shadow-[8px_8px_0_#171717]">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 border-2 border-black bg-[#ffcfdb] px-3 py-1.5 shadow-[3px_3px_0_#171717] mb-6">
              <span className="h-2 w-2 rounded-full bg-[#171717]" />
              <span className="font-mono text-xs font-bold uppercase tracking-widest">WildEcho / Create Account</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2">
              Create <span className="bg-[#f4c542] px-1">Account</span>
            </h1>
            <p className="text-[#625d53]">Join BirdCLEF Classifier</p>
          </div>

          {errors.submit && (
            <div className="bg-[#ffcfdb] border-2 border-black text-[#171717] px-4 py-3 mb-6 font-semibold text-sm shadow-[3px_3px_0_#171717]">
              {errors.submit}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="name" className="block font-mono text-xs font-bold uppercase tracking-wider mb-2">
                Full Name
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="John Doe"
                className={`w-full px-4 py-3 bg-[#fffdf7] border-2 text-[#171717] placeholder-[#9a9387] focus:outline-none focus:ring-2 focus:ring-[#f4c542] focus:ring-offset-2 transition ${
                  errors.name
                    ? 'border-[#c94b5b] focus:ring-[#c94b5b]'
                    : 'border-black'
                }`}
              />
              {errors.name && (
                <p className="text-[#b42335] text-sm font-semibold mt-2">{errors.name}</p>
              )}
            </div>

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
                className={`w-full px-4 py-3 bg-[#fffdf7] border-2 text-[#171717] placeholder-[#9a9387] focus:outline-none focus:ring-2 focus:ring-[#f4c542] focus:ring-offset-2 transition ${
                  errors.email
                    ? 'border-[#c94b5b] focus:ring-[#c94b5b]'
                    : 'border-black'
                }`}
              />
              {errors.email && (
                <p className="text-[#b42335] text-sm font-semibold mt-2">{errors.email}</p>
              )}
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
                className={`w-full px-4 py-3 bg-[#fffdf7] border-2 text-[#171717] placeholder-[#9a9387] focus:outline-none focus:ring-2 focus:ring-[#f4c542] focus:ring-offset-2 transition ${
                  errors.password
                    ? 'border-[#c94b5b] focus:ring-[#c94b5b]'
                    : 'border-black'
                }`}
              />
              {errors.password && (
                <p className="text-[#b42335] text-sm font-semibold mt-2">{errors.password}</p>
              )}
              <p className="text-[#8a8378] font-mono text-[10px] uppercase tracking-wider mt-2">At least 8 characters</p>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block font-mono text-xs font-bold uppercase tracking-wider mb-2">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                className={`w-full px-4 py-3 bg-[#fffdf7] border-2 text-[#171717] placeholder-[#9a9387] focus:outline-none focus:ring-2 focus:ring-[#f4c542] focus:ring-offset-2 transition ${
                  errors.confirmPassword
                    ? 'border-[#c94b5b] focus:ring-[#c94b5b]'
                    : 'border-black'
                }`}
              />
              {errors.confirmPassword && (
                <p className="text-[#b42335] text-sm font-semibold mt-2">{errors.confirmPassword}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-[#f4c542] border-2 border-black shadow-[4px_4px_0_#171717] hover:shadow-[2px_2px_0_#171717] hover:translate-x-[2px] hover:translate-y-[2px] disabled:opacity-60 disabled:cursor-not-allowed font-extrabold uppercase tracking-wide transition duration-200"
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <div className="mt-7 pt-6 border-t-2 border-dashed border-[#c9c1b2] text-center">
            <p className="text-[#625d53]">
              Already have an account?{' '}
              <Link to="/login" className="font-extrabold text-[#171717] underline decoration-2 decoration-[#f4c542] underline-offset-4 hover:bg-[#f4c542] transition">
                Sign in
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
