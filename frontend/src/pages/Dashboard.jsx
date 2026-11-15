import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Fix Leaflet default icon issue
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

const TAXON_COLORS = {
  Aves: '#3b82f6',
  Amphibia: '#10b981',
  Reptilia: '#f59e0b',
  Insecta: '#8b5cf6',
  Mammalia: '#ec4899',
  Osteichthyes: '#06b6d4',
}

const SkeletonRow = () => (
  <div className="space-y-2">
    <div className="h-12 bg-navy-700 rounded animate-pulse"></div>
    <div className="h-12 bg-navy-700 rounded animate-pulse"></div>
  </div>
)

export default function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lifeListSearch, setLifeListSearch] = useState('')
  const [lifeListTaxonFilter, setLifeListTaxonFilter] = useState('all')

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true)
        const response = await axios.get(`${API_URL}/stats`)
        setStats(response.data)
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load dashboard')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-navy-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <h1 className="text-4xl font-bold text-white mb-8">Dashboard</h1>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-navy-800 rounded-lg p-6 border border-navy-700">
                <div className="h-4 bg-navy-700 rounded mb-2"></div>
                <div className="h-8 bg-navy-700 rounded"></div>
              </div>
            ))}
          </div>
          <div className="space-y-8">
            <SkeletonRow />
            <SkeletonRow />
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-navy-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="bg-red-900 border border-red-700 text-red-100 p-6 rounded-lg mb-6">
            {error}
          </div>
          <button
            onClick={() => navigate('/analyze')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
          >
            Upload Your First Recording
          </button>
        </div>
      </div>
    )
  }

  // Empty state
  if (!stats || stats.total_recordings === 0) {
    return (
      <div className="min-h-screen bg-navy-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <h1 className="text-4xl font-bold text-white mb-8">Dashboard</h1>
          <div className="bg-navy-800 rounded-lg p-12 border border-navy-700 text-center">
            <div className="text-6xl mb-4">🎵</div>
            <h2 className="text-2xl font-bold text-white mb-3">No Recordings Yet</h2>
            <p className="text-navy-300 mb-8 max-w-md mx-auto">
              Upload your first audio recording to start building your personal life list and see insights about your bird sightings.
            </p>
            <button
              onClick={() => navigate('/analyze')}
              className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition"
            >
              Upload Your First Audio
            </button>
          </div>
        </div>
      </div>
    )
  }

  const uploadsData = Object.entries(stats.uploads_per_day).map(([date, count]) => ({
    date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    uploads: count,
  }))

  const filteredLifeList = (stats.life_list || []).filter((sp) => {
    const nameMatch =
      sp.name.toLowerCase().includes(lifeListSearch.toLowerCase()) ||
      sp.species_code.toLowerCase().includes(lifeListSearch.toLowerCase())
    const taxonMatch = lifeListTaxonFilter === 'all' || sp.taxon === lifeListTaxonFilter
    return nameMatch && taxonMatch
  })

  const uniqueTaxons = Array.from(new Set(stats.life_list?.map((sp) => sp.taxon) || []))

  return (
    <div className="min-h-screen bg-navy-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-4xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-navy-300 mb-8">Your personal birding statistics and insights</p>

        {/* Stat Tiles */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <div className="bg-navy-800 rounded-lg p-6 border border-navy-700">
            <p className="text-navy-400 text-sm font-medium mb-2">Recordings</p>
            <p className="text-4xl font-bold text-white">{stats.total_recordings}</p>
            <p className="text-navy-400 text-xs mt-2">audio files analyzed</p>
          </div>

          <div className="bg-navy-800 rounded-lg p-6 border border-navy-700">
            <p className="text-navy-400 text-sm font-medium mb-2">Hours Analyzed</p>
            <p className="text-4xl font-bold text-white">
              {(stats.total_duration_sec / 3600).toFixed(1)}
            </p>
            <p className="text-navy-400 text-xs mt-2">total duration</p>
          </div>

          <div className="bg-navy-800 rounded-lg p-6 border border-navy-700">
            <p className="text-navy-400 text-sm font-medium mb-2">Unique Species</p>
            <p className="text-4xl font-bold text-white">{stats.unique_species_count}</p>
            <p className="text-navy-400 text-xs mt-2">in your life list</p>
          </div>

          <div className="bg-navy-800 rounded-lg p-6 border border-navy-700">
            <p className="text-navy-400 text-sm font-medium mb-2">Top Species</p>
            <p className="text-2xl font-bold text-blue-400">
              {stats.top_species?.[0]?.name || 'N/A'}
            </p>
            <p className="text-navy-400 text-xs mt-2">most detected</p>
          </div>
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-12">
          {/* Uploads Over Time */}
          <div className="lg:col-span-2 bg-navy-800 rounded-lg p-6 border border-navy-700">
            <h2 className="text-xl font-bold text-white mb-4">Uploads Over Time (30 days)</h2>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={uploadsData}>
                <defs>
                  <linearGradient id="colorUploads" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                  labelStyle={{ color: '#e2e8f0' }}
                />
                <Area
                  type="monotone"
                  dataKey="uploads"
                  stroke="#3b82f6"
                  fillOpacity={1}
                  fill="url(#colorUploads)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Taxon Breakdown */}
          {Object.keys(stats.taxon_breakdown || {}).length > 0 && (
            <div className="bg-navy-800 rounded-lg p-6 border border-navy-700">
              <h2 className="text-xl font-bold text-white mb-4">Species by Taxon</h2>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={Object.entries(stats.taxon_breakdown).map(([taxon, count]) => ({
                      name: taxon,
                      value: count,
                    }))}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {Object.keys(stats.taxon_breakdown).map((taxon) => (
                      <Cell key={taxon} fill={TAXON_COLORS[taxon] || '#999'} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                    labelStyle={{ color: '#e2e8f0' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Top Species */}
        {stats.top_species && stats.top_species.length > 0 && (
          <div className="bg-navy-800 rounded-lg p-6 border border-navy-700 mb-12">
            <h2 className="text-xl font-bold text-white mb-4">Top 10 Species</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={stats.top_species}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 200 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis type="number" stroke="#94a3b8" />
                <YAxis dataKey="code" type="category" stroke="#94a3b8" width={180} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                  labelStyle={{ color: '#e2e8f0' }}
                  formatter={(value) => `${value} windows`}
                />
                <Bar dataKey="total_windows" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Map */}
        {stats.map_points && stats.map_points.length > 0 && (
          <div className="bg-navy-800 rounded-lg p-6 border border-navy-700 mb-12 overflow-hidden">
            <h2 className="text-xl font-bold text-white mb-4">Sighting Locations</h2>
            <MapContainer
              center={[
                stats.map_points[0]?.lat || 0,
                stats.map_points[0]?.lng || 0,
              ]}
              zoom={4}
              style={{ height: '400px', borderRadius: '0.5rem' }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; OpenStreetMap contributors'
              />
              {stats.map_points.map((point) => (
                <Marker key={point.recording_id} position={[point.lat, point.lng]}>
                  <Popup>
                    <div className="text-sm">
                      <p className="font-semibold text-navy-900">{point.filename}</p>
                      <p className="text-xs text-navy-700 mt-1">
                        {new Date(point.created_at).toLocaleDateString()}
                      </p>
                      <div className="mt-2 space-y-1">
                        {point.species.map((sp, idx) => (
                          <p key={idx} className="text-xs text-navy-700">
                            {sp.name}: {(sp.score * 100).toFixed(0)}%
                          </p>
                        ))}
                      </div>
                      <button
                        onClick={() => navigate(`/results/${point.recording_id}`)}
                        className="mt-3 w-full px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                      >
                        View Results
                      </button>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        )}

        {/* Life List */}
        {stats.life_list && stats.life_list.length > 0 && (
          <div className="bg-navy-800 rounded-lg p-6 border border-navy-700">
            <h2 className="text-xl font-bold text-white mb-4">Life List</h2>

            {/* Filters */}
            <div className="mb-6 flex flex-col sm:flex-row gap-4">
              <input
                type="text"
                placeholder="Search species..."
                value={lifeListSearch}
                onChange={(e) => setLifeListSearch(e.target.value)}
                className="flex-1 px-4 py-2 bg-navy-900 border border-navy-600 rounded text-white placeholder-navy-400 focus:border-blue-500 focus:outline-none"
              />
              <select
                value={lifeListTaxonFilter}
                onChange={(e) => setLifeListTaxonFilter(e.target.value)}
                className="px-4 py-2 bg-navy-900 border border-navy-600 rounded text-white focus:border-blue-500 focus:outline-none"
              >
                <option value="all">All Taxons</option>
                {uniqueTaxons.map((taxon) => (
                  <option key={taxon} value={taxon}>
                    {taxon}
                  </option>
                ))}
              </select>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-navy-700">
                    <th className="px-4 py-3 text-left text-navy-300 font-semibold">Species</th>
                    <th className="px-4 py-3 text-left text-navy-300 font-semibold">Taxon</th>
                    <th className="px-4 py-3 text-left text-navy-300 font-semibold">First Seen</th>
                    <th className="px-4 py-3 text-center text-navy-300 font-semibold">Times Detected</th>
                    <th className="px-4 py-3 text-center text-navy-300 font-semibold">Best Score</th>
                    <th className="px-4 py-3 text-center text-navy-300 font-semibold">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLifeList.map((species) => (
                    <tr key={species.species_code} className="border-b border-navy-700 hover:bg-navy-750 transition">
                      <td className="px-4 py-3">
                        <div>
                          <p className="text-white font-semibold">{species.name}</p>
                          <p className="text-navy-400 text-xs">{species.species_code}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className="inline-block px-2 py-1 rounded text-xs font-semibold text-white"
                          style={{ backgroundColor: TAXON_COLORS[species.taxon] || '#999' }}
                        >
                          {species.taxon}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-navy-300">
                        {species.first_seen
                          ? new Date(species.first_seen).toLocaleDateString()
                          : 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-center text-white font-semibold">
                        {species.times_detected}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-white font-semibold">
                          {(species.best_score * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        {species.most_recent_recording_id && (
                          <button
                            onClick={() => navigate(`/results/${species.most_recent_recording_id}`)}
                            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition"
                          >
                            View
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filteredLifeList.length === 0 && (
                <p className="text-center py-8 text-navy-400">No species match your filters</p>
              )}
            </div>

            <p className="text-navy-400 text-xs mt-4">
              Total: {filteredLifeList.length} of {stats.life_list.length} species
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
