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

  // Fetch recording
  useEffect(() => {
    const fetchRecording = async () => {
      try {
        setLoading(true)
        const response = await axios.get(`${API_URL}/recordings/${id}`)
        setRecording(response.data)

        // Check if still processing
        if (response.data.status !== 'done') {
          setIsProcessing(true)
        }

        // Load feedback
        await loadFeedback()
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load results')
      } finally {
        setLoading(false)
      }
    }

    fetchRecording()
  }, [id])

  // Poll for completion if processing
  useEffect(() => {
    if (!isProcessing || !id) return

    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_URL}/recordings/${id}`)
        setRecording(response.data)

        if (response.data.status === 'done') {
          setIsProcessing(false)
          clearInterval(interval)
          setPollInterval(null)
        }
      } catch (err) {
        console.error('Poll error:', err)
      }
    }, 2000)

    setPollInterval(interval)

    return () => clearInterval(interval)
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
      <div className="min-h-screen bg-navy-900 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
          <div className="text-white">Loading results...</div>
        </div>
      </div>
    )
  }

  // Error state
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
            Back to Analyze
          </button>
        </div>
      </div>
    )
  }

  // No prediction state
  if (!recording || !recording.prediction) {
    return (
      <div className="min-h-screen bg-navy-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {isProcessing ? (
            <div className="bg-blue-900 border border-blue-700 text-blue-100 p-6 rounded-lg mb-6">
              <div className="flex items-center gap-3">
                <div className="inline-block animate-spin rounded-full h-5 w-5 border-b-2 border-blue-300"></div>
                <span>Processing audio... This may take a few minutes.</span>
              </div>
            </div>
          ) : (
            <div className="text-navy-300">No prediction available</div>
          )}
          <button
            onClick={() => navigate('/analyze')}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
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
    <div className="min-h-screen bg-navy-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Analysis Results</h1>
          <div className="flex flex-wrap gap-4 text-navy-300">
            <span>{recording.original_filename}</span>
            <span>•</span>
            <span>{recording.duration_sec?.toFixed(1)}s</span>
            <span>•</span>
            <span>Site {recording.site_id}</span>
            <span>•</span>
            <span>Hour {recording.hour}:00</span>
            {recording.lat && recording.lng && (
              <>
                <span>•</span>
                <span>{recording.lat.toFixed(2)}, {recording.lng.toFixed(2)}</span>
              </>
            )}
          </div>
        </div>

        {/* Taxon Filter */}
        {taxons.length > 1 && (
          <div className="mb-6 flex flex-wrap gap-2">
            <button
              onClick={() => setTaxonFilter('all')}
              className={`px-3 py-1 rounded-full text-sm font-medium transition ${
                taxonFilter === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-navy-700 text-navy-300 hover:bg-navy-600'
              }`}
            >
              All
            </button>
            {taxons.map((taxon) => (
              <button
                key={taxon}
                onClick={() => setTaxonFilter(taxon)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition ${
                  taxonFilter === taxon
                    ? 'bg-blue-600 text-white'
                    : 'bg-navy-700 text-navy-300 hover:bg-navy-600'
                }`}
              >
                {taxon}
              </button>
            ))}
          </div>
        )}

        {/* Waveform */}
        <WaveformHover
          audioUrl={`${API_URL}/recordings/${id}/audio`}
          waveformPeaks={pred.waveform_peaks}
          duration={pred.real_duration_sec}
          prediction={pred}
          onWindowClick={(idx) => console.log('Clicked window', idx)}
          onTimeChange={setCurrentTime}
          selectedSpecies={selectedSpecies}
        />

        {/* Top Species Cards */}
        {topSpecies.length > 0 && (
          <TopSpeciesCards
            topSpecies={topSpecies}
            selectedSpecies={selectedSpecies}
            onSelect={setSelectedSpecies}
            feedback={feedback}
            onFeedback={handleFeedback}
          />
        )}

        {/* Detections Table */}
        <DetectionsTable prediction={pred} selectedSpecies={selectedSpecies} />

        {/* Charts Container */}
        <div id="results-chart" className="space-y-8">
          {/* Heatmap */}
          <HeatmapChart prediction={pred} selectedSpecies={selectedSpecies} />

          {/* Score Chart */}
          <ScoreChart prediction={pred} selectedSpecies={selectedSpecies} />
        </div>

        {/* Spectrogram */}
        <Spectrogram
          recordingId={id}
          currentTime={currentTime}
          duration={pred.real_duration_sec}
        />

        {/* Export */}
        <ExportBar recording={recording} prediction={pred} selectedChart="heatmap" />

        {/* Navigation buttons */}
        <div className="flex gap-4">
          <button
            onClick={() => navigate('/analyze')}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition"
          >
            Analyze Another
          </button>
          <button
            onClick={() => navigate('/history')}
            className="px-6 py-3 bg-navy-800 hover:bg-navy-700 text-white rounded-lg font-semibold border border-navy-600 transition"
          >
            View History
          </button>
        </div>
      </div>
    </div>
  )
}
