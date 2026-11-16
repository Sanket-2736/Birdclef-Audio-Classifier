import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import WaveformHover from '../components/WaveformHover'
import TopSpeciesCards from '../components/TopSpeciesCards'
import DetectionsTable from '../components/DetectionsTable'
import HeatmapChart from '../components/HeatmapChart'
import ScoreChart from '../components/ScoreChart'
import Spectrogram from '../components/Spectrogram'
import ExportBar from '../components/ExportBar'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Results() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [recording, setRecording] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedSpecies, setSelectedSpecies] = useState(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [feedback, setFeedback] = useState({})
  const [isProcessing, setIsProcessing] = useState(false)
  const [pollInterval, setPollInterval] = useState(null)
  const [taxonFilter, setTaxonFilter] = useState('all')
  const [activeTab, setActiveTab] = useState('overview')

  // Fetch recording
  useEffect(() => {
    const fetchRecording = async () => {
      try {
        console.log(`[Results] Initial fetch for recording: ${id}`)
        setLoading(true)
        const response = await axios.get(`${API_URL}/recordings/${id}`)
        console.log('[Results] Initial fetch response:', { status: response.data.status, has_prediction: !!response.data.prediction, progress_stage: response.data.progress_stage, error_message: response.data.error_message })
        setRecording(response.data)

        // Check if still processing
        if (response.data.status !== 'done') {
          console.log(`[Results] Status is "${response.data.status}", starting polling...`)
          setIsProcessing(true)
        } else {
          console.log('[Results] Status is "done", no polling needed')
        }

        // Load feedback
        await loadFeedback()
      } catch (err) {
        console.error('[Results] Initial fetch error:', err)
        setError(err.response?.data?.detail || 'Failed to load results')
      } finally {
        setLoading(false)
      }
    }

    fetchRecording()
  }, [id])

  // Poll for completion if processing
  useEffect(() => {
    if (!isProcessing || !id) {
      console.log(`[Results] Polling disabled: isProcessing=${isProcessing}, id=${id}`)
      return
    }

    console.log(`[Results] Starting polling loop for recording: ${id}`)
    let pollCount = 0

    const interval = setInterval(async () => {
      pollCount++
      try {
        console.log(`[Results] Poll attempt #${pollCount}`)
        const response = await axios.get(`${API_URL}/recordings/${id}`)
        console.log(`[Results] Poll #${pollCount} response:`, { status: response.data.status, progress_stage: response.data.progress_stage, error_message: response.data.error_message, has_prediction: !!response.data.prediction })
        setRecording(response.data)

        if (response.data.status === 'done') {
          console.log(`[Results] Status is DONE, stopping polling after ${pollCount} attempts`)
          setIsProcessing(false)
          clearInterval(interval)
          setPollInterval(null)
        } else if (response.data.status === 'failed') {
          console.log(`[Results] Status is FAILED, stopping polling. Error: ${response.data.error_message}`)
          setError(response.data.error_message || 'Processing failed')
          setIsProcessing(false)
          clearInterval(interval)
          setPollInterval(null)
        }
      } catch (err) {
        console.error(`[Results] Poll #${pollCount} error:`, err.message)
      }
    }, 2000)

    setPollInterval(interval)

    return () => {
      console.log(`[Results] Cleaning up polling interval after ${pollCount} attempts`)
      clearInterval(interval)
    }
  }, [isProcessing, id])

  const loadFeedback = async () => {
    try {
      const response = await axios.get(`${API_URL}/recordings/${id}/feedback`)
      const feedbackMap = {}
      response.data.feedback.forEach((fb) => {
        feedbackMap[fb.species_code] = fb.is_correct
      })
      setFeedback(feedbackMap)
    } catch (err) {
      console.error('Failed to load feedback:', err)
    }
  }

  const handleFeedback = async (code, isCorrect) => {
    try {
      await axios.post(`${API_URL}/recordings/${id}/feedback`, {
        species_code: code,
        is_correct: isCorrect,
      })
      setFeedback((prev) => ({
        ...prev,
        [code]: isCorrect,
      }))
    } catch (err) {
      console.error('Failed to save feedback:', err)
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-[#fff8e8] flex items-center justify-center px-4">
        <div className="text-center">
          <div className="inline-block animate-spin h-12 w-12 border-4 border-black border-t-[#f4c542] mb-4" />
          <div className="font-mono text-sm font-bold uppercase tracking-wider text-[#625d53]">
            Loading results...
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-[#fff8e8]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="bg-[#ffcfdb] border-2 border-black text-[#171717] p-6 mb-6 shadow-[5px_5px_0_#171717] font-semibold">
            {error}
          </div>
          <button
            onClick={() => navigate('/analyze')}
            className="px-5 py-3 bg-[#f4c542] border-2 border-black shadow-[4px_4px_0_#171717] hover:shadow-[2px_2px_0_#171717] hover:translate-x-[2px] hover:translate-y-[2px] font-extrabold uppercase tracking-wide transition"
          >
            Back to Analyze
          </button>
        </div>
      </div>
    )
  }

  // No prediction state
  if (!recording || !recording.prediction) {
    return (
      <div className="min-h-screen bg-[#fff8e8]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {isProcessing ? (
            <div className="bg-[#b9e7ff] border-2 border-black text-[#171717] p-6 mb-6 shadow-[5px_5px_0_#171717]">
              <div className="flex items-center gap-3 font-semibold">
                <div className="inline-block animate-spin h-5 w-5 border-2 border-black border-t-transparent shrink-0" />
                <span>Processing audio... This may take a few minutes.</span>
              </div>
            </div>
          ) : (
            <div className="bg-white border-2 border-black p-6 shadow-[5px_5px_0_#171717] text-[#625d53]">
              No prediction available
            </div>
          )}
          <button
            onClick={() => navigate('/analyze')}
            className="mt-4 px-5 py-3 bg-[#f4c542] border-2 border-black shadow-[4px_4px_0_#171717] hover:shadow-[2px_2px_0_#171717] hover:translate-x-[2px] hover:translate-y-[2px] font-extrabold uppercase tracking-wide transition"
          >
            Back to Analyze
          </button>
        </div>
      </div>
    )
  }

  const pred = recording.prediction
  const topSpecies = (pred.top_species || []).filter((sp) => {
    if (taxonFilter === 'all') return true
    return sp.taxon === taxonFilter
  })

  const taxons = Array.from(new Set(pred.top_species?.map((sp) => sp.taxon) || []))

  return (
    <div className="min-h-screen bg-[#fff8e8] text-[#171717]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-12">
        {/* Header Section */}
        <div className="mb-10">
          <div className="inline-flex items-center gap-2 border-2 border-black bg-[#b9e7ff] px-3 py-1.5 shadow-[3px_3px_0_#171717] mb-5">
            <span className="h-2 w-2 rounded-full bg-[#171717]" />
            <span className="font-mono text-xs font-bold uppercase tracking-widest">WildEcho / Analysis Report</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4">
            Analysis <span className="bg-[#f4c542] px-1">Results</span>
          </h1>
          
          {/* Recording Info Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-white border-2 border-black p-4 shadow-[3px_3px_0_#171717]">
              <div className="text-xs font-mono uppercase text-[#766d5e] mb-1">File</div>
              <div className="font-bold text-sm text-[#171717] truncate">{recording.original_filename}</div>
            </div>
            <div className="bg-white border-2 border-black p-4 shadow-[3px_3px_0_#171717]">
              <div className="text-xs font-mono uppercase text-[#766d5e] mb-1">Duration</div>
              <div className="font-bold text-sm text-[#171717]">{recording.duration_sec?.toFixed(1)}s</div>
            </div>
            <div className="bg-white border-2 border-black p-4 shadow-[3px_3px_0_#171717]">
              <div className="text-xs font-mono uppercase text-[#766d5e] mb-1">Site & Hour</div>
              <div className="font-bold text-sm text-[#171717]">Site {recording.site_id} • {recording.hour}:00</div>
            </div>
            <div className="bg-white border-2 border-black p-4 shadow-[3px_3px_0_#171717]">
              <div className="text-xs font-mono uppercase text-[#766d5e] mb-1">Location</div>
              <div className="font-bold text-sm text-[#171717]">
                {recording.lat && recording.lng ? `${recording.lat.toFixed(2)}, ${recording.lng.toFixed(2)}` : 'N/A'}
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="flex gap-2 border-b-2 border-[#171717] pb-4">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-2 font-bold uppercase tracking-wide border-2 border-black transition ${
                activeTab === 'overview'
                  ? 'bg-[#b9e7ff] shadow-[2px_2px_0_#171717]'
                  : 'bg-white hover:bg-[#f4eddd]'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('details')}
              className={`px-4 py-2 font-bold uppercase tracking-wide border-2 border-black transition ${
                activeTab === 'details'
                  ? 'bg-[#b9e7ff] shadow-[2px_2px_0_#171717]'
                  : 'bg-white hover:bg-[#f4eddd]'
              }`}
            >
              Detailed Analysis
            </button>
            <button
              onClick={() => setActiveTab('export')}
              className={`px-4 py-2 font-bold uppercase tracking-wide border-2 border-black transition ${
                activeTab === 'export'
                  ? 'bg-[#b9e7ff] shadow-[2px_2px_0_#171717]'
                  : 'bg-white hover:bg-[#f4eddd]'
              }`}
            >
              Export & Reports
            </button>
          </div>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <>
            {/* Waveform with Audio Player */}
            <div className="mb-8">
              <WaveformHover
                audioUrl={`${API_URL}/recordings/${id}/audio`}
                waveformPeaks={pred.waveform_peaks}
                duration={pred.real_duration_sec}
                prediction={pred}
                onWindowClick={(idx) => console.log('Clicked window', idx)}
                onTimeChange={setCurrentTime}
                selectedSpecies={selectedSpecies}
              />
            </div>

            {/* Top Species Cards */}
            {topSpecies.length > 0 && (
              <div className="mb-8">
                <div className="mb-4">
                  <h2 className="text-2xl font-black tracking-tight text-[#171717] mb-4">
                    Top Detections
                  </h2>
                </div>
                <TopSpeciesCards
                  topSpecies={topSpecies}
                  selectedSpecies={selectedSpecies}
                  onSelect={setSelectedSpecies}
                  feedback={feedback}
                  onFeedback={handleFeedback}
                />
              </div>
            )}

            {/* Taxon Filter */}
            {taxons.length > 1 && (
              <div className="mb-8 border-2 border-black bg-white p-4 shadow-[4px_4px_0_#171717]">
                <div className="font-mono text-xs font-bold uppercase tracking-wider mb-3">Filter by taxon</div>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => setTaxonFilter('all')}
                    className={`px-4 py-2 border-2 border-black text-sm font-extrabold uppercase tracking-wide transition ${
                      taxonFilter === 'all'
                        ? 'bg-[#f4c542] shadow-[2px_2px_0_#171717]'
                        : 'bg-[#fff8e8] hover:bg-[#f4eddd]'
                    }`}
                  >
                    All
                  </button>
                  {taxons.map((taxon) => (
                    <button
                      key={taxon}
                      onClick={() => setTaxonFilter(taxon)}
                      className={`px-4 py-2 border-2 border-black text-sm font-extrabold uppercase tracking-wide transition ${
                        taxonFilter === taxon
                          ? 'bg-[#b9e7ff] shadow-[2px_2px_0_#171717]'
                          : 'bg-[#fff8e8] hover:bg-[#f4eddd]'
                      }`}
                    >
                      {taxon}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Summary Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
              <div className="bg-white border-2 border-black p-5 shadow-[4px_4px_0_#171717]">
                <div className="text-xs font-mono uppercase text-[#766d5e] mb-2">Species Detected</div>
                <div className="text-3xl font-black text-[#171717]">{topSpecies.length}</div>
              </div>
              <div className="bg-white border-2 border-black p-5 shadow-[4px_4px_0_#171717]">
                <div className="text-xs font-mono uppercase text-[#766d5e] mb-2">Valid Windows</div>
                <div className="text-3xl font-black text-[#171717]">{pred.valid_windows || 0}</div>
              </div>
              <div className="bg-white border-2 border-black p-5 shadow-[4px_4px_0_#171717]">
                <div className="text-xs font-mono uppercase text-[#766d5e] mb-2">Top Confidence</div>
                <div className="text-3xl font-black text-[#171717]">
                  {topSpecies.length > 0 ? `${(topSpecies[0].max_score * 100).toFixed(0)}%` : 'N/A'}
                </div>
              </div>
            </div>

            {/* Heatmap */}
            <div className="mb-8">
              <HeatmapChart prediction={pred} selectedSpecies={selectedSpecies} />
            </div>
          </>
        )}

        {/* Details Tab */}
        {activeTab === 'details' && (
          <>
            {/* Detections Table */}
            <div className="mb-8">
              <DetectionsTable prediction={pred} selectedSpecies={selectedSpecies} />
            </div>

            {/* Charts */}
            <div id="results-chart" className="space-y-8 mb-8">
              <ScoreChart prediction={pred} selectedSpecies={selectedSpecies} />
            </div>

            {/* Spectrogram */}
            <div className="mb-8">
              <Spectrogram
                recordingId={id}
                currentTime={currentTime}
                duration={pred.real_duration_sec}
              />
            </div>
          </>
        )}

        {/* Export Tab */}
        {activeTab === 'export' && (
          <div className="mb-8">
            <ExportBar recording={recording} prediction={pred} selectedChart="heatmap" />
          </div>
        )}

        {/* Navigation Footer */}
        <div className="border-t-2 border-black pt-8 flex flex-col sm:flex-row gap-4">
          <button
            onClick={() => navigate('/analyze')}
            className="px-6 py-3 bg-[#f4c542] border-2 border-black shadow-[4px_4px_0_#171717] hover:shadow-[2px_2px_0_#171717] hover:translate-x-[2px] hover:translate-y-[2px] font-extrabold uppercase tracking-wide transition"
          >
            ← Analyze Another
          </button>
          <button
            onClick={() => navigate('/history')}
            className="px-6 py-3 bg-[#b9e7ff] border-2 border-black shadow-[4px_4px_0_#171717] hover:shadow-[2px_2px_0_#171717] hover:translate-x-[2px] hover:translate-y-[2px] font-extrabold uppercase tracking-wide transition"
          >
            View History →
          </button>
        </div>
      </div>
    </div>
  )
}
