export default function DetectionsTable({ prediction, selectedSpecies }) {
  const windows = prediction?.windows || []
  const validWindows = windows.filter((w) => !w.is_padding)

  // Build top species for display
  const allSpecies = new Set()
  validWindows.forEach((w) => {
    if (w.top_k) {
      w.top_k.forEach((sp) => allSpecies.add(sp.code))
    }
  })

  const speciesList = Array.from(allSpecies).slice(0, 10) // Top 10 species

  return (
    <div className="bg-navy-800 rounded-lg p-6 border border-navy-700 mb-8 overflow-x-auto">
      <h2 className="text-2xl font-bold text-white mb-6">Window-by-Window Detections</h2>

      <table className="w-full text-sm text-navy-200 border-collapse">
        <thead>
          <tr className="border-b border-navy-700">
            <th className="px-4 py-3 text-left text-white font-semibold bg-navy-900">
              Window
            </th>
            <th className="px-4 py-3 text-left text-white font-semibold bg-navy-900">
              Time
            </th>
            {speciesList.map((code) => (
              <th
                key={code}
                className={`px-3 py-3 text-center text-xs font-semibold bg-navy-900 border-l border-navy-700 ${
                  selectedSpecies === code ? 'text-blue-400' : ''
                }`}
                title={code}
              >
                {code.substring(0, 6)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {validWindows.map((window, idx) => {
            const startTime = idx * 5
            const endTime = Math.min((idx + 1) * 5, prediction.real_duration_sec)

            return (
              <tr
                key={idx}
                className={`border-b border-navy-700 hover:bg-navy-900 transition ${
                  selectedSpecies ? 'hover:bg-navy-750' : ''
                }`}
              >
                <td className="px-4 py-3 font-semibold text-white bg-navy-900">
                  {idx}
                </td>
                <td className="px-4 py-3 text-navy-300">
                  {startTime.toFixed(0)}-{endTime.toFixed(0)}s
                </td>
                {speciesList.map((code) => {
                  const detection = window.top_k?.find((sp) => sp.code === code)
                  const score = detection?.score || 0

                  return (
                    <td
                      key={`${idx}-${code}`}
                      className={`px-3 py-3 text-center border-l border-navy-700 ${
                        selectedSpecies === code ? 'bg-blue-900 bg-opacity-30' : ''
                      }`}
                    >
                      {score > 0 ? (
                        <div
                          className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                            score > 0.8
                              ? 'bg-green-600 text-white'
                              : score > 0.6
                              ? 'bg-yellow-600 text-white'
                              : 'bg-orange-600 text-white'
                          }`}
                        >
                          {(score * 100).toFixed(0)}%
                        </div>
                      ) : (
                        <span className="text-navy-500">-</span>
                      )}
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
      </table>

      <p className="text-navy-400 text-xs mt-4">
        Showing top {speciesList.length} species. Each window is 5 seconds.
      </p>
    </div>
  )
}
