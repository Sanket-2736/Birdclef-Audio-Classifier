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
        {/* Header */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 border-2 border-black bg-[#b9e7ff] px-3 py-1.5 shadow-[3px_3px_0_#171717] mb-5">
            <span className="h-2 w-2 rounded-full bg-[#171717]" />
            <span className="font-mono text-xs font-bold uppercase tracking-widest">WildEcho / Analysis Report</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-3">
            Analysis <span className="bg-[#f4c542] px-1">Results</span>
          </h1>
          <div className="flex flex-wrap gap-x-3 gap-y-2 text-sm text-[#625d53]">
            <span className="font-semibold text-[#171717]">{recording.original_filename}</span>
            <span aria-hidden="true">•</span>
            <span>{recording.duration_sec?.toFixed(1)}s</span>
            <span aria-hidden="true">•</span>
            <span>Site {recording.site_id}</span>
            <span aria-hidden="true">•</span>
            <span>Hour {recording.hour}:00</span>
            {recording.lat && recording.lng && (
              <>
                <span aria-hidden="true">•</span>
                <span>{recording.lat.toFixed(2)}, {recording.lng.toFixed(2)}</span>
              </>
            )}
          </div>
        </div>

        {/* Taxon Filter */}
        {taxons.length > 1 && (
          <div className="mb-7 border-2 border-black bg-white p-4 shadow-[4px_4px_0_#171717]">
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

        {/* Waveform */}
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
            <TopSpeciesCards
              topSpecies={topSpecies}
              selectedSpecies={selectedSpecies}
              onSelect={setSelectedSpecies}
              feedback={feedback}
              onFeedback={handleFeedback}
            />
          </div>
        )}

        {/* Detections Table */}
        <div className="mb-8">
          <DetectionsTable prediction={pred} selectedSpecies={selectedSpecies} />
        </div>

        {/* Charts Container */}
        <div id="results-chart" className="space-y-8 mb-8">
          {/* Heatmap */}
          <HeatmapChart prediction={pred} selectedSpecies={selectedSpecies} />

          {/* Score Chart */}
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

        {/* Export */}
        <div className="mb-10">
          <ExportBar recording={recording} prediction={pred} selectedChart="heatmap" />
        </div>

        {/* Navigation buttons */}
        <div className="flex flex-col sm:flex-row gap-4">
          <button
            onClick={() => navigate('/analyze')}
            className="px-6 py-3 bg-[#f4c542] border-2 border-black shadow-[4px_4px_0_#171717] hover:shadow-[2px_2px_0_#171717] hover:translate-x-[2px] hover:translate-y-[2px] font-extrabold uppercase tracking-wide transition"
          >
            Analyze Another
          </button>
          <button
            onClick={() => navigate('/history')}
            className="px-6 py-3 bg-[#b9e7ff] border-2 border-black shadow-[4px_4px_0_#171717] hover:shadow-[2px_2px_0_#171717] hover:translate-x-[2px] hover:translate-y-[2px] font-extrabold uppercase tracking-wide transition"
          >
            View History
          </button>
        </div>
      </div>
    </div>
  )
}
