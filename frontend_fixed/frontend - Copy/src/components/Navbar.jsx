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
    <nav className="bg-navy-900 border-b border-navy-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center">
            <span className="text-2xl font-bold text-blue-400">🐦 BirdCLEF</span>
          </Link>

          <div className="hidden md:flex items-center gap-6">
            {/* Public Pages */}
            <Link
              to="/how-it-works"
              className="text-navy-200 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition"
            >
              How It Works
            </Link>
            <Link
              to="/about"
              className="text-navy-200 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition"
            >
              About
            </Link>
            <Link
              to="/contact"
              className="text-navy-200 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition"
            >
              Contact
            </Link>

            {isAuthenticated ? (
              <>
                <div className="border-l border-navy-700 pl-6 flex items-center gap-4">
                  <Link
                    to="/analyze"
                    className="text-navy-200 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition"
                  >
                    Analyze
                  </Link>
                  <Link
                    to="/history"
                    className="text-navy-200 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition"
                  >
                    History
                  </Link>
                  <Link
                    to="/dashboard"
                    className="text-navy-200 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition"
                  >
                    Dashboard
                  </Link>
                </div>

                <div className="flex items-center gap-3 pl-4 border-l border-navy-700">
                  <span className="text-navy-200 text-sm">{user?.name}</span>
                  <button
                    onClick={handleLogout}
                    className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm font-medium transition"
                  >
                    Logout
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="border-l border-navy-700 pl-6 flex items-center gap-3">
                  <Link
                    to="/login"
                    className="text-navy-200 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition"
                  >
                    Login
                  </Link>
                  <Link
                    to="/register"
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition"
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
