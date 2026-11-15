import { useState, useCallback } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function useHistory() {
  const [recordings, setRecordings] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchRecordings = useCallback(
    async (page = 1, pageSize = 10, filters = {}) => {
      setLoading(true)
      setError(null)

      try {
        const params = new URLSearchParams()
        params.append('page', page)
        params.append('page_size', pageSize)
        
        if (filters.q) params.append('q', filters.q)
        if (filters.status) params.append('status', filters.status)
        if (filters.date_from) params.append('date_from', filters.date_from)
        if (filters.date_to) params.append('date_to', filters.date_to)

        const response = await axios.get(`${API_URL}/recordings?${params}`)
        setRecordings(response.data.items)
        setTotal(response.data.total)
        return response.data
      } catch (err) {
        const errorMsg = err.response?.data?.detail || err.message || 'Failed to fetch recordings'
        setError(errorMsg)
        throw err
      } finally {
        setLoading(false)
      }
    },
    []
  )

  const deleteRecording = useCallback(async (recordingId) => {
    try {
      await axios.delete(`${API_URL}/recordings/${recordingId}`)
      setRecordings(recordings.filter(r => r.id !== recordingId))
      setTotal(total - 1)
      return true
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to delete recording'
      setError(errorMsg)
      throw err
    }
  }, [recordings, total])

  return {
    recordings,
    total,
    loading,
    error,
    fetchRecordings,
    deleteRecording,
  }
}
