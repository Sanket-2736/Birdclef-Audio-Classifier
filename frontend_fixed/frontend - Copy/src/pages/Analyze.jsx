import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useRecordingUpload, PROGRESS_STAGES } from '../hooks/useRecordingUpload'
import ProgressStepper from '../components/ProgressStepper'

export default function Analyze() {
  const navigate = useNavigate()
  const { uploadRecording, pollStatus, error: uploadError } = useRecordingUpload()

  const [file, setFile] = useState(null)
  const [timedOut, setTimedOut] = useState(false)
  const [siteId, setSiteId] = useState(0)
  const [hour, setHour] = useState(12)
  const [lat, setLat] = useState('')
  const [lng, setLng] = useState('')
  const [uploading, setUploading] = useState(false)
  const [recordingId, setRecordingId] = useState(null)
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [pollInterval, setPollInterval] = useState(null)
  const [duplicateDialog, setDuplicateDialog] = useState(null)

  // Validate file on change
  const validateFile = (selectedFile) => {
    if (!selectedFile) {
      setError(null)
      return true
    }

    const maxSizeMB = 100
    const maxSizeBytes = maxSizeMB * 1024 * 1024
    const allowedExt = ['wav', 'ogg', 'mp3', 'flac']

    const ext = selectedFile.name.split('.').pop().toLowerCase()
    if (!allowedExt.includes(ext)) {
      setError(`Invalid format. Allowed: ${allowedExt.join(', ')}`)
      return false
    }

    if (selectedFile.size > maxSizeBytes) {
      setError(`File too large (${(selectedFile.size / 1024 / 1024).toFixed(1)} MB). Max: ${maxSizeMB} MB`)
      return false
    }

    setError(null)
    return true
  }

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile && validateFile(selectedFile)) {
      setFile(selectedFile)
    } else {
      setFile(null)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    console.log('[Analyze] Form submitted')

    if (!file) {
      setError('Please select a file')
      return
    }

    if (!(-90 <= parseFloat(lat || 0) <= 90) || !(-180 <= parseFloat(lng || 0) <= 180)) {
      setError('Invalid latitude/longitude')
      return
    }

    setUploading(true)

    try {
      console.log('[Analyze] Uploading file:', { filename: file.name, size: file.size, siteId, hour })
      const result = await uploadRecording(
        file,
        parseInt(siteId),
        parseInt(hour),
        lat ? parseFloat(lat) : undefined,
        lng ? parseFloat(lng) : undefined
      )
      console.log('[Analyze] Upload result:', result)

      // Check for duplicate
      if (result.duplicate) {
        console.log('[Analyze] File is duplicate')
        setDuplicateDialog(result)
        return
      }

      console.log('[Analyze] Upload successful, recording ID:', result.id, 'Status:', result.status)
      setRecordingId(result.id)
      setStatus(result.status)

      // Start polling for status
      let pollCount = 0
let failCount = 0
const MAX_POLLS = 400 // 400 × 1.5 s = 10 minutes
const interval = setInterval(async () => {
  pollCount++
  try {
    const statusResult = await pollStatus(result.id)
    failCount = 0
    setStatus(statusResult)

    if (statusResult.status === 'done') {
      clearInterval(interval); setPollInterval(null)
    } else if (statusResult.status === 'failed') {
      clearInterval(interval); setPollInterval(null)
      setError(statusResult.error_message || 'Inference failed during processing')
    } else if (pollCount >= MAX_POLLS) {
      clearInterval(interval); setPollInterval(null)
      setTimedOut(true)
      setError('Still processing after 10 minutes. You can check again, or look in History.')
    }
  } catch (err) {
    // tolerate brief network blips instead of giving up on the first error
    failCount++
    if (failCount >= 5) {
      clearInterval(interval); setPollInterval(null)
      setTimedOut(true)
      setError('Lost contact with the server. You can check again.')
    }
  }
}, 4000)

      setPollInterval(interval)
      console.log('[Analyze] Started polling')
    } catch (err) {
      console.error('[Analyze] Upload error:', err)
      setError(uploadError || err.message)
    } finally {
      setUploading(false)
    }
  }

  // Navigate to results when done
  useEffect(() => {
    if (status?.status === 'done' && recordingId) {
      // Wait a moment for DB to be consistent
      setTimeout(() => {
        navigate(`/results/${recordingId}`)
      }, 500)
    }
  }, [status?.status, recordingId, navigate])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollInterval) clearInterval(pollInterval)
    }
  }, [pollInterval])

  return (
    <div className="min-h-screen bg-[#fff8e8] text-[#171717]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-10">
          <div className="inline-flex items-center gap-2 border-2 border-black bg-[#b9e7ff] px-3 py-1.5 shadow-[3px_3px_0_#171717] mb-5">
            <span className="h-2 w-2 rounded-full bg-[#171717]" />
            <span className="font-mono text-xs font-bold uppercase tracking-widest">WildEcho / Audio Lab</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-3">Analyze Audio<span className="text-[#f4c542]">.</span></h1>
          <p className="text-[#55514a] text-base sm:text-lg">Upload an audio file to classify bird species</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Form */}
          <div className="bg-white border-2 border-black p-6 sm:p-8 h-fit shadow-[7px_7px_0_#171717]">
            <div className="flex items-center justify-between gap-3 mb-7">
              <h2 className="text-xl font-extrabold">Upload recording</h2>
              <span className="bg-[#f4c542] border-2 border-black px-2 py-1 font-mono text-[10px] font-bold uppercase tracking-wider">01 / Input</span>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* File Input */}
              <div>
                <label className="block text-sm font-bold mb-3">
                  Audio File
                </label>
                <div className="border-2 border-dashed border-black bg-[#fff8e8] p-6 text-center hover:bg-[#fff1c2] transition cursor-pointer">
                  <input
                    type="file"
                    accept=".wav,.ogg,.mp3,.flac"
                    onChange={handleFileChange}
                    disabled={uploading || recordingId}
                    className="hidden"
                    id="file-input"
                  />
                  <label htmlFor="file-input" className="cursor-pointer">
                    <div className="text-4xl mb-3">📁</div>
                    <p className="font-bold break-all">
                      {file ? file.name : 'Click to upload'}
                    </p>
                    <p className="text-[#777168] text-xs font-mono mt-2">
                      WAV, OGG, MP3, or FLAC up to 100 MB
                    </p>
                  </label>
                </div>
              </div>

              {/* Site & Hour */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="site" className="block text-sm font-bold mb-2">
                    Site ID (0-19)
                  </label>
                  <input
                    id="site"
                    type="number"
                    min="0"
                    max="19"
                    value={siteId}
                    onChange={(e) => setSiteId(e.target.value)}
                    disabled={uploading || recordingId}
                    className="w-full px-3 py-3 bg-[#fff8e8] border-2 border-black text-[#171717] focus:outline-none focus:ring-2 focus:ring-[#f4c542] disabled:opacity-50"
                  />
                </div>
                <div>
                  <label htmlFor="hour" className="block text-sm font-bold mb-2">
                    Hour (0-23)
                  </label>
                  <input
                    id="hour"
                    type="number"
                    min="0"
                    max="23"
                    value={hour}
                    onChange={(e) => setHour(e.target.value)}
                    disabled={uploading || recordingId}
                    className="w-full px-3 py-3 bg-[#fff8e8] border-2 border-black text-[#171717] focus:outline-none focus:ring-2 focus:ring-[#f4c542] disabled:opacity-50"
                  />
                </div>
              </div>

              {/* Location */}
              <div>
                <div className="flex justify-between items-center gap-3 mb-3">
                  <label className="text-sm font-bold">Location (optional)</label>
                  <button
                    type="button"
                    onClick={() => {
                      if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition((position) => {
                          setLat(position.coords.latitude.toFixed(6))
                          setLng(position.coords.longitude.toFixed(6))
                        }, () => {
                          setError('Could not get your location. Please enable location services.')
                        })
                      } else {
                        setError('Geolocation not supported by your browser')
                      }
                    }}
                    disabled={uploading || recordingId}
                    className="text-xs px-3 py-2 bg-[#b9e7ff] border-2 border-black font-bold hover:bg-[#91d8fa] transition disabled:opacity-50"
                  >
                    📍 Use My Location
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="lat" className="block text-xs font-mono font-bold text-[#777168] mb-2">
                      Latitude
                    </label>
                    <input
                      id="lat"
                      type="number"
                      step="0.01"
                      placeholder="-90 to 90"
                      value={lat}
                      onChange={(e) => setLat(e.target.value)}
                      disabled={uploading || recordingId}
                      className="w-full px-3 py-3 bg-[#fff8e8] border-2 border-black text-[#171717] placeholder-[#aaa398] focus:outline-none focus:ring-2 focus:ring-[#f4c542] disabled:opacity-50"
                    />
                  </div>
                  <div>
                    <label htmlFor="lng" className="block text-xs font-mono font-bold text-[#777168] mb-2">
                      Longitude
                    </label>
                    <input
                      id="lng"
                      type="number"
                      step="0.01"
                      placeholder="-180 to 180"
                      value={lng}
                      onChange={(e) => setLng(e.target.value)}
                      disabled={uploading || recordingId}
                      className="w-full px-3 py-3 bg-[#fff8e8] border-2 border-black text-[#171717] placeholder-[#aaa398] focus:outline-none focus:ring-2 focus:ring-[#f4c542] disabled:opacity-50"
                    />
                  </div>
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className="p-4 bg-[#ffe0df] border-2 border-black text-[#9f2424] font-semibold shadow-[3px_3px_0_#171717]">
                  {error}
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={!file || uploading || recordingId}
                className="w-full py-4 px-4 bg-[#f4c542] border-2 border-black text-[#171717] font-extrabold uppercase tracking-wide shadow-[4px_4px_0_#171717] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_#171717] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-x-0 disabled:hover:translate-y-0 disabled:hover:shadow-[4px_4px_0_#171717] transition"
              >
                {uploading ? 'Uploading...' : 'Analyze Audio'}
              </button>
            </form>

            {/* Duplicate Dialog */}
            {duplicateDialog && (
              <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                <div className="bg-[#fff8e8] border-2 border-black p-6 max-w-md w-full shadow-[8px_8px_0_#000]">
                  <div className="inline-block bg-[#ffb6c8] border-2 border-black px-2 py-1 font-mono text-[10px] font-bold uppercase tracking-wider mb-4">Duplicate detected</div>
                  <h2 className="text-xl font-extrabold mb-3">File Already Uploaded</h2>
                  <p className="text-[#55514a] mb-6">
                    You've already uploaded this file. Would you like to view the previous result?
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={() => {
                        setDuplicateDialog(null)
                        setFile(null)
                      }}
                      className="flex-1 py-3 px-4 bg-white border-2 border-black font-bold hover:bg-[#eee8d9] transition"
                    >
                      Upload Again
                    </button>
                    <button
                      onClick={() => navigate(`/results/${duplicateDialog.existing_id}`)}
                      className="flex-1 py-3 px-4 bg-[#b9e7ff] border-2 border-black font-bold hover:bg-[#91d8fa] transition"
                    >
                      View Results
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Progress Stepper */}
          {recordingId && (
            <ProgressStepper
              currentStage={status?.progress_stage}
              error={status?.error_message}
              isDone={status?.status === 'done'}
            />
          )}
        </div>
      </div>
    </div>
  )
}
