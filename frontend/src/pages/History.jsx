import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useHistory } from '../hooks/useHistory'
import '../styles/History.css'

const statusColors = {
  queued: '#f59e0b',
  processing: '#3b82f6',
  done: '#10b981',
  failed: '#ef4444',
}

const statusLabels = {
  queued: 'Queued',
  processing: 'Processing',
  done: 'Completed',
  failed: 'Failed',
}

function SkeletonRow() {
  return (
    <div className="recording-card skeleton">
      <div className="skeleton-header"></div>
      <div className="skeleton-text"></div>
      <div className="skeleton-text" style={{ width: '60%' }}></div>
    </div>
  )
}

export default function History() {
  const navigate = useNavigate()
  const { recordings, total, loading, error, fetchRecordings, deleteRecording } = useHistory()
  
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [searchQ, setSearchQ] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [debouncedQ, setDebouncedQ] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [refreshIntervals, setRefreshIntervals] = useState({})

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQ(searchQ)
      setPage(1)
    }, 500)
    return () => clearTimeout(timer)
  }, [searchQ])

  // Fetch recordings when filters/page change
  useEffect(() => {
    fetchRecordings(page, pageSize, {
      q: debouncedQ,
      status: statusFilter,
      date_from: dateFrom,
      date_to: dateTo,
    })
  }, [page, pageSize, debouncedQ, statusFilter, dateFrom, dateTo, fetchRecordings])

  // Auto-refresh processing items every 2 seconds
  useEffect(() => {
    const processingIds = recordings
      .filter(r => r.status === 'processing' || r.status === 'queued')
      .map(r => r.id)

    if (processingIds.length === 0) return

    const timer = setInterval(() => {
      fetchRecordings(page, pageSize, {
        q: debouncedQ,
        status: statusFilter,
        date_from: dateFrom,
        date_to: dateTo,
      })
    }, 2000)

    return () => clearInterval(timer)
  }, [page, pageSize, debouncedQ, statusFilter, dateFrom, dateTo, recordings, fetchRecordings])

  const handleDelete = async (recordingId) => {
    setDeleting(true)
    try {
      await deleteRecording(recordingId)
      setDeleteConfirm(null)
    } catch (err) {
      console.error('Delete failed:', err)
    } finally {
      setDeleting(false)
    }
  }

  const handleResultsClick = (recordingId) => {
    navigate(`/results/${recordingId}`)
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="history-container">
      <div className="history-header">
        <h1>Upload History</h1>
        <p className="subtitle">View and manage your audio recordings</p>
      </div>

      {/* Filters */}
      <div className="filters">
        {/* Search */}
        <div className="filter-group">
          <input
            type="text"
            placeholder="Search by filename or species..."
            value={searchQ}
            onChange={e => setSearchQ(e.target.value)}
            className="search-input"
          />
        </div>

        {/* Status filter */}
        <div className="filter-group">
          <select
            value={statusFilter}
            onChange={e => {
              setStatusFilter(e.target.value)
              setPage(1)
            }}
            className="filter-select"
          >
            <option value="">All Status</option>
            <option value="queued">Queued</option>
            <option value="processing">Processing</option>
            <option value="done">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        {/* Date range */}
        <div className="filter-group">
          <input
            type="date"
            value={dateFrom}
            onChange={e => {
              setDateFrom(e.target.value)
              setPage(1)
            }}
            className="filter-input"
            placeholder="From"
          />
          <span>to</span>
          <input
            type="date"
            value={dateTo}
            onChange={e => {
              setDateTo(e.target.value)
              setPage(1)
            }}
            className="filter-input"
            placeholder="To"
          />
        </div>

        {/* Clear filters */}
        {(searchQ || statusFilter || dateFrom || dateTo) && (
          <button
            onClick={() => {
              setSearchQ('')
              setStatusFilter('')
              setDateFrom('')
              setDateTo('')
              setPage(1)
            }}
            className="btn-clear-filters"
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Empty state */}
      {!loading && recordings.length === 0 && (
        <div className="empty-state">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z" />
          </svg>
          <h2>No recordings yet</h2>
          <p>Upload your first audio file to get started.</p>
          <button onClick={() => navigate('/analyze')} className="btn-primary">
            Upload Audio
          </button>
        </div>
      )}

      {/* Recordings list */}
      <div className="recordings-list">
        {loading ? (
          <>
            <SkeletonRow />
            <SkeletonRow />
            <SkeletonRow />
          </>
        ) : (
          recordings.map(recording => (
            <div key={recording.id} className="recording-card">
              <div className="card-header" onClick={() => handleResultsClick(recording.id)}>
                <div className="card-title-section">
                  <h3 className="card-title" title={recording.original_filename}>
                    {recording.original_filename}
                  </h3>
                  <span
                    className="status-badge"
                    style={{ backgroundColor: statusColors[recording.status] }}
                  >
                    {recording.status === 'processing' && (
                      <span className="pulse"></span>
                    )}
                    {statusLabels[recording.status]}
                    {recording.status === 'processing' && ` (${recording.progress_stage})`}
                  </span>
                </div>
              </div>

              <div className="card-info">
                <div className="info-row">
                  <span className="info-label">Date:</span>
                  <span>{new Date(recording.created_at).toLocaleDateString()}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Duration:</span>
                  <span>{recording.duration_sec.toFixed(1)}s</span>
                </div>
                {recording.site_id >= 0 && (
                  <div className="info-row">
                    <span className="info-label">Site:</span>
                    <span>{recording.site_id}</span>
                  </div>
                )}
              </div>

              {/* Top species */}
              {recording.top_species && recording.top_species.length > 0 && (
                <div className="species-chips">
                  {recording.top_species.map((sp, idx) => (
                    <div key={idx} className="species-chip">
                      <span className="species-name">{sp.name}</span>
                      <span className="species-score">{(sp.score * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              )}

              <div className="card-actions">
                <button
                  onClick={() => handleResultsClick(recording.id)}
                  className="btn-secondary"
                >
                  View Results
                </button>
                <button
                  onClick={() => setDeleteConfirm(recording.id)}
                  className="btn-danger"
                  disabled={deleting}
                >
                  Delete
                </button>
              </div>

              {/* Delete confirmation modal */}
              {deleteConfirm === recording.id && (
                <div className="delete-modal">
                  <div className="modal-content">
                    <h3>Delete Recording?</h3>
                    <p>This action cannot be undone. The audio file and all results will be permanently deleted.</p>
                    <div className="modal-actions">
                      <button
                        onClick={() => setDeleteConfirm(null)}
                        className="btn-secondary"
                        disabled={deleting}
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleDelete(recording.id)}
                        className="btn-danger"
                        disabled={deleting}
                      >
                        {deleting ? 'Deleting...' : 'Delete'}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1 || loading}
            className="btn-secondary"
          >
            Previous
          </button>
          <span className="page-info">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages || loading}
            className="btn-secondary"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
