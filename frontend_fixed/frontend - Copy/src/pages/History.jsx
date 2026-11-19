import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useHistory } from '../hooks/useHistory'

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
    <div className="bg-white border-2 border-black p-5 shadow-[4px_4px_0_#171717] animate-pulse space-y-3">
      <div className="h-5 w-2/3 bg-[#e8dfc9] border border-black" />
      <div className="h-4 w-full bg-[#eee8d9]" />
      <div className="h-4 w-3/5 bg-[#eee8d9]" />
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
    <div className="min-h-screen bg-[#fff8e8] text-[#171717]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-9">
          <div className="inline-flex items-center gap-2 border-2 border-black bg-[#b9e7ff] px-3 py-1.5 shadow-[3px_3px_0_#171717] mb-5">
            <span className="h-2 w-2 rounded-full bg-[#171717]" />
            <span className="font-mono text-xs font-bold uppercase tracking-widest">WildEcho / Archive</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-3">
            Upload History<span className="text-[#f4c542]">.</span>
          </h1>
          <p className="text-[#625d53] text-base sm:text-lg">View and manage your audio recordings</p>
        </div>

        {/* Filters */}
        <div className="bg-white border-2 border-black p-5 sm:p-6 mb-8 shadow-[5px_5px_0_#171717]">
          <div className="font-mono text-xs font-bold uppercase tracking-widest mb-4">Filter recordings</div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {/* Search */}
            <div className="filter-group">
              <input
                type="text"
                placeholder="Search by filename or species..."
                value={searchQ}
                onChange={e => setSearchQ(e.target.value)}
                className="w-full min-w-0 px-4 py-3 bg-[#fff8e8] border-2 border-black text-[#171717] placeholder-[#8b857a] focus:outline-none focus:ring-2 focus:ring-[#f4c542]"
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
                className="w-full px-4 py-3 bg-[#fff8e8] border-2 border-black text-[#171717] focus:outline-none focus:ring-2 focus:ring-[#f4c542]"
              >
                <option value="">All Status</option>
                <option value="queued">Queued</option>
                <option value="processing">Processing</option>
                <option value="done">Completed</option>
                <option value="failed">Failed</option>
              </select>
            </div>

            {/* Date range */}
            <div className="filter-group flex items-center gap-2">
              <input
                type="date"
                value={dateFrom}
                onChange={e => {
                  setDateFrom(e.target.value)
                  setPage(1)
                }}
                className="min-w-0 w-full px-3 py-3 bg-[#fff8e8] border-2 border-black text-[#171717] focus:outline-none focus:ring-2 focus:ring-[#f4c542]"
                placeholder="From"
              />
              <span className="text-xs font-mono font-bold text-[#625d53]">to</span>
              <input
                type="date"
                value={dateTo}
                onChange={e => {
                  setDateTo(e.target.value)
                  setPage(1)
                }}
                className="min-w-0 w-full px-3 py-3 bg-[#fff8e8] border-2 border-black text-[#171717] focus:outline-none focus:ring-2 focus:ring-[#f4c542]"
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
                className="px-4 py-3 bg-[#ffcfdb] border-2 border-black font-bold uppercase text-xs tracking-wide shadow-[3px_3px_0_#171717] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0_#171717] transition"
              >
                Clear Filters
              </button>
            )}
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="bg-[#ffe0df] border-2 border-black text-[#9f2424] p-5 mb-6 shadow-[4px_4px_0_#171717]">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Empty state */}
        {!loading && recordings.length === 0 && (
          <div className="bg-white border-2 border-black p-10 sm:p-12 text-center shadow-[7px_7px_0_#171717] mb-8">
            <div className="text-6xl mb-4">🎵</div>
            <h2 className="text-2xl font-extrabold mb-3">No recordings yet</h2>
            <p className="text-[#625d53] mb-8 max-w-md mx-auto">
              Upload your first audio file to get started.
            </p>
            <button
              onClick={() => navigate('/analyze')}
              className="px-8 py-3 bg-[#f4c542] border-2 border-black font-extrabold uppercase tracking-wide shadow-[4px_4px_0_#171717] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_#171717] transition"
            >
              Upload Audio
            </button>
          </div>
        )}

        {/* Recordings list */}
        <div className="space-y-5">
          {loading ? (
            <>
              <SkeletonRow />
              <SkeletonRow />
              <SkeletonRow />
            </>
          ) : (
            recordings.map(recording => (
              <div key={recording.id} className="bg-white border-2 border-black p-5 sm:p-6 shadow-[5px_5px_0_#171717]">
                <div
                  className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 cursor-pointer"
                  onClick={() => handleResultsClick(recording.id)}
                >
                  <div className="min-w-0">
                    <h3 className="text-lg sm:text-xl font-extrabold break-words" title={recording.original_filename}>
                      {recording.original_filename}
                    </h3>
                  </div>
                  <span
                    className="inline-flex items-center gap-2 self-start border-2 border-black px-3 py-1 text-xs font-bold uppercase tracking-wide text-black"
                    style={{ backgroundColor: statusColors[recording.status] }}
                  >
                    {recording.status === 'processing' && (
                      <span className="h-2 w-2 rounded-full bg-black animate-pulse" />
                    )}
                    {statusLabels[recording.status]}
                    {recording.status === 'processing' && ` (${recording.progress_stage})`}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-5 text-sm">
                  <div className="bg-[#fff8e8] border-2 border-black p-3">
                    <span className="block text-[10px] font-mono font-bold uppercase tracking-widest text-[#777168] mb-1">Date</span>
                    <span className="font-semibold">{new Date(recording.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="bg-[#fff8e8] border-2 border-black p-3">
                    <span className="block text-[10px] font-mono font-bold uppercase tracking-widest text-[#777168] mb-1">Duration</span>
                    <span className="font-semibold">{recording.duration_sec.toFixed(1)}s</span>
                  </div>
                  {recording.site_id >= 0 && (
                    <div className="bg-[#fff8e8] border-2 border-black p-3">
                      <span className="block text-[10px] font-mono font-bold uppercase tracking-widest text-[#777168] mb-1">Site</span>
                      <span className="font-semibold">{recording.site_id}</span>
                    </div>
                  )}
                </div>

                {/* Top species */}
                {recording.top_species && recording.top_species.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-5">
                    {recording.top_species.map((sp, idx) => (
                      <div key={idx} className="inline-flex items-center gap-2 bg-[#d9f4d2] border-2 border-black px-3 py-2 text-sm">
                        <span className="font-bold">{sp.name}</span>
                        <span className="font-mono text-xs font-bold">{(sp.score * 100).toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                )}

                <div className="flex flex-wrap gap-3 mt-6 pt-5 border-t-2 border-dashed border-[#b8b0a1]">
                  <button
                    onClick={() => handleResultsClick(recording.id)}
                    className="px-4 py-2.5 bg-[#b9e7ff] border-2 border-black font-bold text-sm shadow-[3px_3px_0_#171717] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0_#171717] transition"
                  >
                    View Results
                  </button>
                  <button
                    onClick={() => setDeleteConfirm(recording.id)}
                    className="px-4 py-2.5 bg-[#ffcfdb] border-2 border-black font-bold text-sm shadow-[3px_3px_0_#171717] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0_#171717] transition"
                    disabled={deleting}
                  >
                    Delete
                  </button>
                </div>

                {/* Delete confirmation modal */}
                {deleteConfirm === recording.id && (
                  <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                    <div className="bg-[#fff8e8] border-2 border-black p-6 max-w-md w-full shadow-[8px_8px_0_#000]">
                      <div className="inline-block bg-[#ffcfdb] border-2 border-black px-2 py-1 font-mono text-[10px] font-bold uppercase tracking-wider mb-4">Confirm action</div>
                      <h3 className="text-xl font-extrabold mb-3">Delete Recording?</h3>
                      <p className="text-[#625d53] mb-6">
                        This action cannot be undone. The audio file and all results will be permanently deleted.
                      </p>
                      <div className="flex gap-3">
                        <button
                          onClick={() => setDeleteConfirm(null)}
                          className="flex-1 px-4 py-3 bg-white border-2 border-black font-bold hover:bg-[#eee8d9] transition"
                          disabled={deleting}
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => handleDelete(recording.id)}
                          className="flex-1 px-4 py-3 bg-[#ffcfdb] border-2 border-black font-bold hover:bg-[#ffb6c8] transition"
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
          <div className="flex flex-wrap items-center justify-center gap-5 mt-9">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1 || loading}
              className="px-5 py-3 bg-white border-2 border-black font-bold shadow-[3px_3px_0_#171717] disabled:opacity-40 disabled:cursor-not-allowed hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0_#171717] transition"
            >
              Previous
            </button>
            <span className="font-mono text-sm font-bold">Page {page} of {totalPages}</span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages || loading}
              className="px-5 py-3 bg-[#f4c542] border-2 border-black font-bold shadow-[3px_3px_0_#171717] disabled:opacity-40 disabled:cursor-not-allowed hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0_#171717] transition"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
