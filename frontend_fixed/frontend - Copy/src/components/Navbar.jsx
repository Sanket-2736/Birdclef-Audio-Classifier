import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="bg-[#fff3d6] border-b border-[#171717]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center">
            <span className="text-2xl font-bold text-[#171717]">🐦 WildEcho</span>
          </Link>

          <div className="hidden md:flex items-center gap-6">
            {/* Public Pages */}
            <Link
              to="/how-it-works"
              className="text-[#302b24] hover:text-[#171717] px-3 py-2 rounded-none-none text-sm font-bold border-2 border-[#171717] shadow-[3px_3px_0_#171717] transition hover:translate-x-[1px] hover:translate-y-[1px]"
            >
              How It Works
            </Link>
            <Link
              to="/about"
              className="text-[#302b24] hover:text-[#171717] px-3 py-2 rounded-none-none text-sm font-bold border-2 border-[#171717] shadow-[3px_3px_0_#171717] transition hover:translate-x-[1px] hover:translate-y-[1px]"
            >
              About
            </Link>
            <Link
              to="/contact"
              className="text-[#302b24] hover:text-[#171717] px-3 py-2 rounded-none-none text-sm font-bold border-2 border-[#171717] shadow-[3px_3px_0_#171717] transition hover:translate-x-[1px] hover:translate-y-[1px]"
            >
              Contact
            </Link>

            {isAuthenticated ? (
              <>
                <div className="border-l border-[#171717] pl-6 flex items-center gap-4">
                  <Link
                    to="/analyze"
                    className="text-[#302b24] hover:text-[#171717] px-3 py-2 rounded-none-none text-sm font-bold border-2 border-[#171717] shadow-[3px_3px_0_#171717] transition hover:translate-x-[1px] hover:translate-y-[1px]"
                  >
                    Analyze
                  </Link>
                  <Link
                    to="/history"
                    className="text-[#302b24] hover:text-[#171717] px-3 py-2 rounded-none-none text-sm font-bold border-2 border-[#171717] shadow-[3px_3px_0_#171717] transition hover:translate-x-[1px] hover:translate-y-[1px]"
                  >
                    History
                  </Link>
                  <Link
                    to="/dashboard"
                    className="text-[#302b24] hover:text-[#171717] px-3 py-2 rounded-none-none text-sm font-bold border-2 border-[#171717] shadow-[3px_3px_0_#171717] transition hover:translate-x-[1px] hover:translate-y-[1px]"
                  >
                    Dashboard
                  </Link>
                </div>

                <div className="flex items-center gap-3 pl-4 border-l border-[#171717]">
                  <span className="text-[#302b24] text-sm">{user?.name}</span>
                  <button
                    onClick={handleLogout}
                    className="px-3 py-1 bg-[#ffcfdb] hover:bg-[#ffb8ca] text-[#171717] rounded-none text-sm font-bold border-2 border-[#171717] shadow-[3px_3px_0_#171717] transition hover:translate-x-[1px] hover:translate-y-[1px]"
                  >
                    Logout
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="border-l border-[#171717] pl-6 flex items-center gap-3">
                  <Link
                    to="/login"
                    className="text-[#302b24] hover:text-[#171717] px-3 py-2 rounded-none-none text-sm font-bold border-2 border-[#171717] shadow-[3px_3px_0_#171717] transition hover:translate-x-[1px] hover:translate-y-[1px]"
                  >
                    Login
                  </Link>
                  <Link
                    to="/register"
                    className="px-4 py-2 bg-[#b9e7ff] hover:bg-[#a4dcf7] text-[#171717] rounded-none-none text-sm font-bold border-2 border-[#171717] shadow-[3px_3px_0_#171717] transition hover:translate-x-[1px] hover:translate-y-[1px]"
                  >
                    Sign Up
                  </Link>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
