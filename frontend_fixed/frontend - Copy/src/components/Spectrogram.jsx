import { useEffect, useRef, useState } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Spectrogram({ recordingId, currentTime, duration }) {
  const containerRef = useRef(null)
  const [spectrogramUrl, setSpectrogramUrl] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('full')
  const [windowImages, setWindowImages] = useState([])
  const [metadata, setMetadata] = useState(null)
  const [selectedWindow, setSelectedWindow] = useState(null)

  // Fetch spectrogram metadata
  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        setLoading(true)
        const token = localStorage.getItem('token')
        
        const response = await axios.get(
          `${API_URL}/recordings/${recordingId}/logmel`,
          {
            headers: token ? { 'Authorization': `Bearer ${token}` } : {},
          }
        )
        
        setMetadata(response.data)
        
        if (response.data.spectrogram_image_url) {
          setSpectrogramUrl(response.data.spectrogram_image_url)
        }
        
        if (response.data.window_images && response.data.window_images.length > 0) {
          setWindowImages(response.data.window_images)
        }
        
        if (!response.data.spectrogram_image_url) {
          setError('Spectrogram image not yet generated')
        }
      } catch (err) {
        console.error('[Spectrogram] Error fetching metadata:', err)
        setError(err.response?.data?.detail || 'Failed to load spectrogram metadata')
      } finally {
        setLoading(false)
      }
    }

    if (recordingId) {
      fetchMetadata()
    }
  }, [recordingId])

  if (error && activeTab === 'full') {
    return (
      <div className="bg-white rounded-none-none p-6 border-2 border-[#171717] shadow-[5px_5px_0_#171717] mb-8">
        <h2 className="text-2xl font-bold text-[#171717] mb-4">Acoustic Analysis</h2>
        <div className="bg-[#ffcfdb] border-2 border-[#dc2626] p-4 rounded-none text-[#dc2626] text-sm">
          <p className="font-semibold">{error}</p>
          <p className="text-xs mt-2">Spectrograms are generated automatically after analysis completes. Try refreshing in a moment.</p>
        </div>
      </div>
    )
  }

  // Calculate playhead position
  const playheadPercent = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div className="bg-white rounded-none-none p-6 border-2 border-[#171717] shadow-[5px_5px_0_#171717] mb-8">
      <h2 className="text-2xl font-bold text-[#171717] mb-4">Acoustic Analysis</h2>

      {/* Tab Navigation */}
      {(spectrogramUrl || windowImages.length > 0 || metadata) && (
        <div className="flex gap-2 mb-6 border-b-2 border-[#171717] pb-4">
          <button
            onClick={() => setActiveTab('full')}
            className={`px-4 py-2 font-bold uppercase text-sm tracking-wide border-2 border-[#171717] rounded-none transition ${
              activeTab === 'full'
                ? 'bg-[#b9e7ff] shadow-[2px_2px_0_#171717]'
                : 'bg-white hover:bg-[#f4eddd]'
            }`}
          >
            Full Recording
          </button>
          
          {windowImages.length > 0 && (
            <button
              onClick={() => setActiveTab('windows')}
              className={`px-4 py-2 font-bold uppercase text-sm tracking-wide border-2 border-[#171717] rounded-none transition ${
                activeTab === 'windows'
                  ? 'bg-[#b9e7ff] shadow-[2px_2px_0_#171717]'
                  : 'bg-white hover:bg-[#f4eddd]'
              }`}
            >
              Windows ({windowImages.length})
            </button>
          )}
          
          {metadata && (
            <button
              onClick={() => setActiveTab('features')}
              className={`px-4 py-2 font-bold uppercase text-sm tracking-wide border-2 border-[#171717] rounded-none transition ${
                activeTab === 'features'
                  ? 'bg-[#b9e7ff] shadow-[2px_2px_0_#171717]'
                  : 'bg-white hover:bg-[#f4eddd]'
              }`}
            >
              Acoustic Features
            </button>
          )}
        </div>
      )}

      {/* Full Recording Spectrogram */}
      {activeTab === 'full' && (
        <>
          {loading && (
            <div className="bg-[#fff3d6] rounded-none h-64 flex items-center justify-center text-[#766d5e] border-2 border-[#171717]">
              <div className="flex flex-col items-center gap-3">
                <div className="animate-spin h-8 w-8 border-4 border-[#766d5e] border-t-[#f4c542]" />
                <span>Generating acoustic analysis...</span>
              </div>
            </div>
          )}

          {spectrogramUrl && !loading && (
            <div
              ref={containerRef}
              className="relative bg-[#fff3d6] rounded-none overflow-hidden border-2 border-[#171717]"
              style={{ aspectRatio: '16 / 4' }}
            >
              <img
                src={`${API_URL}${spectrogramUrl}?token=${localStorage.getItem('token')}`}
                alt="Log-Mel Spectrogram"
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
                className="absolute top-2 text-xs text-white bg-black bg-opacity-70 px-2 py-1 rounded-none pointer-events-none font-mono"
                style={{ left: `${playheadPercent}%`, transform: 'translateX(-50%)' }}
              >
                {currentTime.toFixed(1)}s
              </div>
            </div>
          )}

          <p className="text-[#766d5e] text-xs mt-4">
            <strong>Log-Mel Spectrogram:</strong> Frequency (Hz, log scale) vs Time (seconds). Color intensity represents relative power in dB.
            Blue playhead shows current audio position.
          </p>
        </>
      )}

      {/* Window Spectrograms */}
      {activeTab === 'windows' && (
        <div className="space-y-4">
          {windowImages.map((win, idx) => (
            <div key={idx} className="border-2 border-[#171717] rounded-none overflow-hidden">
              <button
                onClick={() => setSelectedWindow(selectedWindow === idx ? null : idx)}
                className="w-full text-left p-3 bg-[#f4eddd] hover:bg-[#e8dcc8] font-bold text-sm text-[#171717] transition border-b-2 border-[#171717]"
              >
                Window {win.window_index}: {win.window_index * 5}-{(win.window_index + 1) * 5}s {selectedWindow === idx ? '▼' : '▶'}
              </button>
              
              {selectedWindow === idx && (
                <div className="p-4 bg-[#fff8e8]">
                  <img
                    src={`${API_URL}${win.url}?token=${localStorage.getItem('token')}`}
                    alt={`Window ${win.window_index}`}
                    className="w-full h-auto border-2 border-[#171717]"
                    onError={() => console.error(`Failed to load window ${win.window_index}`)}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Acoustic Features Summary */}
      {activeTab === 'features' && metadata && (
        <div className="space-y-6">
          {/* Audio Properties */}
          <div className="bg-[#f4eddd] border-2 border-[#171717] p-4 rounded-none">
            <h3 className="font-bold text-[#171717] mb-3 text-sm uppercase">Audio Properties</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
              <div>
                <p className="text-[#766d5e] text-xs">Sample Rate</p>
                <p className="font-bold text-[#171717]">{metadata.audio_properties?.sample_rate_hz?.toLocaleString()} Hz</p>
              </div>
              <div>
                <p className="text-[#766d5e] text-xs">Duration</p>
                <p className="font-bold text-[#171717]">{metadata.audio_properties?.duration_sec?.toFixed(2)}s</p>
              </div>
              <div>
                <p className="text-[#766d5e] text-xs">Peak Amplitude</p>
                <p className="font-bold text-[#171717]">{metadata.audio_properties?.peak_amplitude?.toFixed(4)}</p>
              </div>
              <div>
                <p className="text-[#766d5e] text-xs">RMS Amplitude</p>
                <p className="font-bold text-[#171717]">{metadata.audio_properties?.rms_amplitude?.toFixed(4)}</p>
              </div>
              <div>
                <p className="text-[#766d5e] text-xs">Channels</p>
                <p className="font-bold text-[#171717]">{metadata.audio_properties?.num_channels}</p>
              </div>
            </div>
          </div>

          {/* Spectral Features */}
          {metadata.spectral_features && Object.keys(metadata.spectral_features).length > 0 && (
            <div className="bg-[#f4eddd] border-2 border-[#171717] p-4 rounded-none">
              <h3 className="font-bold text-[#171717] mb-3 text-sm uppercase">Spectral Characteristics</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                {Object.entries(metadata.spectral_features).map(([key, vals]) => (
                  <div key={key} className="bg-white border border-[#171717] p-2 rounded-none">
                    <p className="text-[#766d5e] text-xs font-mono">{key.replace(/_/g, ' ').toUpperCase()}</p>
                    <p className="font-bold text-[#171717] mt-1">
                      μ: {vals.mean?.toFixed(2)} | σ: {vals.std?.toFixed(2)}
                    </p>
                    <p className="text-[#514a40] text-xs mt-1">
                      Range: {vals.min?.toFixed(2)} — {vals.max?.toFixed(2)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Mel Features */}
          {metadata.mel_features && (
            <div className="bg-[#f4eddd] border-2 border-[#171717] p-4 rounded-none">
              <h3 className="font-bold text-[#171717] mb-3 text-sm uppercase">Mel-Spectrogram Analysis</h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm mb-4">
                <div>
                  <p className="text-[#766d5e] text-xs">Mel Bands</p>
                  <p className="font-bold text-[#171717]">{metadata.mel_features?.n_mels}</p>
                </div>
                <div>
                  <p className="text-[#766d5e] text-xs">FFT Size</p>
                  <p className="font-bold text-[#171717]">{metadata.mel_features?.n_fft}</p>
                </div>
                <div>
                  <p className="text-[#766d5e] text-xs">Hop Length</p>
                  <p className="font-bold text-[#171717]">{metadata.mel_features?.hop_length}</p>
                </div>
                <div>
                  <p className="text-[#766d5e] text-xs">Max Frequency</p>
                  <p className="font-bold text-[#171717]">{(metadata.mel_features?.fmax_hz / 1000).toFixed(1)}kHz</p>
                </div>
              </div>
              
              {metadata.mel_features?.dominant_mel_bands && (
                <div className="bg-white border border-[#171717] p-3 rounded-none">
                  <p className="text-[#766d5e] text-xs font-mono mb-2">Top 5 Energy Bands</p>
                  <div className="space-y-1">
                    {metadata.mel_features.dominant_mel_bands.map((band, idx) => (
                      <p key={idx} className="text-sm font-mono text-[#171717]">
                        Band {band.band_index}: {band.frequency_hz?.toFixed(0)}Hz (Energy: {band.energy?.toFixed(4)})
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* MFCC Features */}
          {metadata.mfcc_features && (
            <div className="bg-[#f4eddd] border-2 border-[#171717] p-4 rounded-none">
              <h3 className="font-bold text-[#171717] mb-3 text-sm uppercase">MFCC Coefficients ({metadata.mfcc_features?.n_mfcc} coeffs)</h3>
              <div className="text-xs font-mono space-y-1">
                <p className="text-[#766d5e]">Mean: {metadata.mfcc_features?.mfcc_mean?.slice(0, 5).map(v => v.toFixed(2)).join(', ')}...</p>
                <p className="text-[#766d5e]">Std: {metadata.mfcc_features?.mfcc_std?.slice(0, 5).map(v => v.toFixed(2)).join(', ')}...</p>
              </div>
            </div>
          )}

          <p className="text-[#766d5e] text-xs bg-[#fff3d6] border-2 border-[#f4c542] p-3 rounded-none">
            <strong>Note:</strong> These acoustic measurements show what was measured in the audio during the same time intervals where species were detected.
            They are temporal associations, not independently validated species-specific signatures.
          </p>
        </div>
      )}
    </div>
  )
}
