import { PROGRESS_STAGES } from '../hooks/useRecordingUpload'

export default function ProgressStepper({ currentStage, error, isDone }) {
  const currentIndex = PROGRESS_STAGES.indexOf(currentStage || '')

  return (
    <div className="bg-navy-800 rounded-lg p-6 border border-navy-700">
      <h3 className="text-lg font-semibold text-white mb-6">Processing Pipeline</h3>

      <div className="space-y-4">
        {PROGRESS_STAGES.map((stage, idx) => {
          let status = 'pending'
          if (idx < currentIndex) status = 'completed'
          if (idx === currentIndex && !isDone && !error) status = 'active'
          if (error && idx === currentIndex) status = 'error'

          return (
            <div key={stage} className="flex items-center gap-4">
              {/* Circle indicator */}
              <div
                className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-semibold text-sm transition ${
                  status === 'completed'
                    ? 'bg-green-600 text-white'
                    : status === 'active'
                      ? 'bg-blue-600 text-white animate-pulse'
                      : status === 'error'
                        ? 'bg-red-600 text-white'
                        : 'bg-navy-700 text-navy-400'
                }`}
              >
                {status === 'completed' ? '✓' : status === 'error' ? '✕' : idx + 1}
              </div>

              {/* Stage name */}
              <div className="flex-grow">
                <p
                  className={`font-medium transition ${
                    status === 'active'
                      ? 'text-blue-400'
                      : status === 'completed'
                        ? 'text-green-400'
                        : status === 'error'
                          ? 'text-red-400'
                          : 'text-navy-300'
                  }`}
                >
                  {stage}
                </p>
              </div>

              {/* Progress indicator */}
              {status === 'active' && <div className="text-blue-400">●</div>}
            </div>
          )
        })}
      </div>

      {/* Error message */}
      {error && (
        <div className="mt-6 p-4 bg-red-900 border border-red-700 text-red-100 rounded">
          <p className="font-semibold">Error:</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Success message */}
      {isDone && !error && (
        <div className="mt-6 p-4 bg-green-900 border border-green-700 text-green-100 rounded">
          <p className="font-semibold">✓ Analysis complete!</p>
        </div>
      )}
    </div>
  )
}
