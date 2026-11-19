import { useState, useCallback } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Progress stages in order
export const PROGRESS_STAGES = [
  'Loading audio',
  'Perch embeddings',
  'ProtoSSM',
  'MLP probes',
  'ResidualSSM',
  'SED detection',
  'Blending results',
  'Post-processing',
  'Completed',
]

export function useRecordingUpload() {
  const [recording, setRecording] = useState(null)
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const uploadRecording = useCallback(
    async (file, siteId, hour, lat, lng) => {
      setError(null)
      setLoading(true)

      try {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('site_id', siteId)
        formData.append('hour', hour)
        if (lat !== undefined && lat !== null) formData.append('lat', lat)
        if (lng !== undefined && lng !== null) formData.append('lng', lng)

        const response = await axios.post(`${API_URL}/recordings/`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })

        setRecording(response.data)
        setStatus(response.data.status)
        return response.data
      } catch (err) {
        const errorMsg = err.response?.data?.detail || err.message || 'Upload failed'
        setError(errorMsg)
        throw err
      } finally {
        setLoading(false)
      }
    },
    []
  )

  const pollStatus = useCallback(async (recordingId) => {
    try {
      console.log(`[pollStatus] Fetching status for recording: ${recordingId}`)
      const response = await axios.get(`${API_URL}/recordings/${recordingId}/status`)
      console.log(`[pollStatus] Response for ${recordingId}:`, { status: response.data.status, progress_stage: response.data.progress_stage, error_message: response.data.error_message })
      setStatus(response.data)
      return response.data
    } catch (err) {
      console.error(`[pollStatus] Error fetching status:`, err.message)
      if (err.response?.status === 404) {
        setError('Recording not found')
      } else {
        setError(err.response?.data?.detail || 'Failed to fetch status')
      }
      throw err
    }
  }, [])

  const fetchRecording = useCallback(async (recordingId) => {
    try {
      const response = await axios.get(`${API_URL}/recordings/${recordingId}`)
      setRecording(response.data)
      setStatus(response.data.status)
      return response.data
    } catch (err) {
      if (err.response?.status === 404) {
        setError('Recording not found')
      } else {
        setError(err.response?.data?.detail || 'Failed to fetch recording')
      }
      throw err
    }
  }, [])

  return {
    recording,
    status,
    error,
    loading,
    uploadRecording,
    pollStatus,
    fetchRecording,
  }
}
