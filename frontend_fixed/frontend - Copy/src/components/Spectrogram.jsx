import { useEffect, useRef, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Spectrogram({ recordingId, currentTime, duration }) {
  const containerRef = useRef(null)
  const [spectrogramUrl, setSpectrogramUrl] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch spectrogram
  useEffect(() => {
    const fetchSpectrogram = async () => {
      try {
        setLoading(true)
        // Add cache-busting query if needed
        const url = `${API_URL}/recordings/${recordingId}/spectrogram?t=${Date.now()}`
        setSpectrogramUrl(url)
      } catch (err) {
        setError('Failed to load spectrogram')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    if (recordingId) {
      fetchSpectrogram()
    }
  }, [recordingId])

  if (error) {
    return (
      <div className="bg-white rounded-none-none p-6 border-2 border-[#171717] shadow-[5px_5px_0_#171717] mb-8">
        <h2 className="text-2xl font-bold text-[#171717] mb-4">Mel Spectrogram</h2>
        <div className="text-[#766d5e]">{error}</div>
      </div>
    )
  }

  // Calculate playhead position
  const playheadPercent = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div className="bg-white rounded-none-none p-6 border-2 border-[#171717] shadow-[5px_5px_0_#171717] mb-8">
      <h2 className="text-2xl font-bold text-[#171717] mb-4">Mel Spectrogram</h2>

      {loading && (
        <div className="bg-[#fff3d6] rounded-none h-64 flex items-center justify-center text-[#766d5e]">
          Loading spectrogram...
        </div>
      )}

      {spectrogramUrl && !loading && (
        <div
          ref={containerRef}
          className="relative bg-[#fff3d6] rounded-none overflow-hidden"
          style={{ aspectRatio: '16 / 4' }}
        >
          <img
            src={spectrogramUrl}
            alt="Mel Spectrogram"
            className="w-full h-full object-cover"
            onError={() => setError('Failed to load spectrogram image')}
          />

          {/* Playhead line */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-blue-500 pointer-events-none"
            style={{
              left: `${playheadPercent}%`,
              boxShadow: '0 0 10px rgba(59, 130, 246, 0.5)',
            }}
          />

          {/* Time tooltip */}
          <div
            className="absolute top-2 text-xs text-[#171717] bg-black bg-opacity-50 px-2 py-1 rounded-none pointer-events-none"
            style={{ left: `${playheadPercent}%`, transform: 'translateX(-50%)' }}
          >
            {currentTime.toFixed(1)}s
          </div>
        </div>
      )}

      <p className="text-[#766d5e] text-xs mt-4">
        Frequency vs Time representation. Blue line shows current playback position.
      </p>
    </div>
  )
}
