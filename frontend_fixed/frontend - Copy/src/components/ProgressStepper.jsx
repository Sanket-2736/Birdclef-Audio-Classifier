import { PROGRESS_STAGES } from '../hooks/useRecordingUpload'

export default function ProgressStepper({ currentStage, error, isDone }) {
  const currentIndex = PROGRESS_STAGES.indexOf(currentStage || '')

  return (
    <div className="bg-white rounded-none-none p-6 border-2 border-[#171717] shadow-[5px_5px_0_#171717]">
      <h3 className="text-lg font-semibold text-[#171717] mb-6">Processing Pipeline</h3>

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
                className={`flex-shrink-0 w-8 h-8 rounded-none-full flex items-center justify-center font-semibold text-sm transition ${
                  status === 'completed'
                    ? 'bg-[#d9f4d2] text-[#171717]'
                    : status === 'active'
                      ? 'bg-[#b9e7ff] text-[#171717] animate-pulse'
                      : status === 'error'
                        ? 'bg-[#ffcfdb] text-[#171717]'
                        : 'bg-[#f4ead4] text-[#766d5e]'
                }`}
              >
                {status === 'completed' ? '✓' : status === 'error' ? '✕' : idx + 1}
              </div>

              {/* Stage name */}
              <div className="flex-grow">
                <p
                  className={`font-bold border-2 border-[#171717] shadow-[3px_3px_0_#171717] transition hover:translate-x-[1px] hover:translate-y-[1px] ${
                    status === 'active'
                      ? 'text-[#171717]'
                      : status === 'completed'
                        ? 'text-green-400'
                        : status === 'error'
                          ? 'text-red-400'
                          : 'text-[#514a40]'
                  }`}
                >
                  {stage}
                </p>
              </div>

              {/* Progress indicator */}
              {status === 'active' && <div className="text-[#171717]">●</div>}
            </div>
          )
        })}
      </div>

      {/* Error message */}
      {error && (
        <div className="mt-6 p-4 bg-red-900 border border-red-700 text-red-100 rounded-none">
          <p className="font-semibold">Error:</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Success message */}
      {isDone && !error && (
        <div className="mt-6 p-4 bg-green-900 border border-green-700 text-green-100 rounded-none">
          <p className="font-semibold">✓ Analysis complete!</p>
        </div>
      )}
    </div>
  )
}
