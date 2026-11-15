import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useRecordingUpload, PROGRESS_STAGES } from '../hooks/useRecordingUpload'
import ProgressStepper from '../components/ProgressStepper'

export default function Analyze() {
  const navigate = useNavigate()
  const { uploadRecording, pollStatus, error: uploadError } = useRecordingUpload()

  const [file, setFile] = useState(null)
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
      const result = await uploadRecording(
        file,
        parseInt(siteId),
        parseInt(hour),
        lat ? parseFloat(lat) : undefined,
        lng ? parseFloat(lng) : undefined
      )

      // Check for duplicate
      if (result.duplicate) {
        setDuplicateDialog(result)
        return
      }

      setRecordingId(result.id)
      setStatus(result.status)

      // Start polling for status
      const interval = setInterval(async () => {
        try {
          const statusResult = await pollStatus(result.id)
          setStatus(statusResult)

          // Stop polling when done or failed
          if (statusResult.status === 'done' || statusResult.status === 'failed') {
            clearInterval(interval)
            setPollInterval(null)
          }
        } catch (err) {
          clearInterval(interval)
          setPollInterval(null)
        }
      }, 1500) // Poll every 1.5 seconds

      setPollInterval(interval)
    } catch (err) {
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
    <div className="min-h-screen bg-navy-900">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-4xl font-bold text-white mb-2">Analyze Audio</h1>
        <p className="text-navy-300 mb-8">Upload an audio file to classify bird species</p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Form */}
          <div className="bg-navy-800 rounded-lg p-8 border border-navy-700 h-fit">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* File Input */}
              <div>
                <label className="block text-sm font-medium text-navy-200 mb-3">
                  Audio File
                </label>
                <div className="border-2 border-dashed border-navy-600 rounded-lg p-6 text-center hover:border-blue-500 transition cursor-pointer">
                  <input
                    type="file"
                    accept=".wav,.ogg,.mp3,.flac"
                    onChange={handleFileChange}
                    disabled={uploading || recordingId}
                    className="hidden"
                    id="file-input"
                  />
                  <label htmlFor="file-input" className="cursor-pointer">
                    <div className="text-4xl mb-2">📁</div>
                    <p className="text-navy-200 font-medium">
                      {file ? file.name : 'Click to upload'}
                    </p>
                    <p className="text-navy-400 text-sm mt-1">
                      WAV, OGG, MP3, or FLAC up to 100 MB
                    </p>
                  </label>
                </div>
              </div>

              {/* Site & Hour */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="site" className="block text-sm font-medium text-navy-200 mb-1">
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
                    className="w-full px-3 py-2 bg-navy-700 border border-navy-600 rounded text-white focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="hour" className="block text-sm font-medium text-navy-200 mb-1">
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
                    className="w-full px-3 py-2 bg-navy-700 border border-navy-600 rounded text-white focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              {/* Location */}
              <div>
                <div className="flex justify-between items-center mb-3">
                  <label className="text-sm font-medium text-navy-200">Location (optional)</label>
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
                    className="text-xs px-2 py-1 bg-navy-700 hover:bg-navy-600 text-blue-400 hover:text-blue-300 rounded transition disabled:opacity-50"
                  >
                    📍 Use My Location
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="lat" className="block text-xs text-navy-400 mb-1">
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
                      className="w-full px-3 py-2 bg-navy-700 border border-navy-600 rounded text-white placeholder-navy-400 focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label htmlFor="lng" className="block text-xs text-navy-400 mb-1">
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
                      className="w-full px-3 py-2 bg-navy-700 border border-navy-600 rounded text-white placeholder-navy-400 focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className="p-4 bg-red-900 border border-red-700 text-red-100 rounded">
                  {error}
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={!file || uploading || recordingId}
                className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 text-white font-semibold rounded-lg transition"
              >
                {uploading ? 'Uploading...' : 'Analyze Audio'}
              </button>
            </form>

            {/* Duplicate Dialog */}
            {duplicateDialog && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-navy-800 border border-navy-700 rounded-lg p-6 max-w-md">
                  <h2 className="text-xl font-bold text-white mb-3">File Already Uploaded</h2>
                  <p className="text-navy-300 mb-6">
                    You've already uploaded this file. Would you like to view the previous result?
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={() => {
                        setDuplicateDialog(null)
                        setFile(null)
                      }}
                      className="flex-1 py-2 px-4 bg-navy-700 hover:bg-navy-600 text-white font-medium rounded transition"
                    >
                      Upload Again
                    </button>
                    <button
                      onClick={() => navigate(`/results/${duplicateDialog.existing_id}`)}
                      className="flex-1 py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded transition"
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

