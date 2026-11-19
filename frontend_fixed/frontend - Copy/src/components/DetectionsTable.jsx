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
    <div className="bg-white rounded-none-none p-6 border-2 border-[#171717] shadow-[5px_5px_0_#171717] mb-8 overflow-x-auto">
      <h2 className="text-2xl font-black tracking-tight text-[#171717] mb-6">Window-by-Window Detections</h2>

      <table className="w-full text-sm text-[#302b24] border-collapse">
        <thead>
          <tr className="border-b border-[#171717]">
            <th className="px-4 py-3 text-left text-[#171717] font-semibold bg-[#fff3d6]">
              Window
            </th>
            <th className="px-4 py-3 text-left text-[#171717] font-semibold bg-[#fff3d6]">
              Time
            </th>
            {speciesList.map((code) => (
              <th
                key={code}
                className={`px-3 py-3 text-center text-xs font-semibold bg-[#fff3d6] border-l border-[#171717] ${
                  selectedSpecies === code ? 'text-[#171717]' : ''
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
                className={`border-b border-[#171717] hover:bg-[#fff3d6] transition ${
                  selectedSpecies ? 'hover:bg-[#fff3d6]' : ''
                }`}
              >
                <td className="px-4 py-3 font-semibold text-[#171717] bg-[#fff3d6]">
                  {idx}
                </td>
                <td className="px-4 py-3 text-[#514a40]">
                  {startTime.toFixed(0)}-{endTime.toFixed(0)}s
                </td>
                {speciesList.map((code) => {
                  const detection = window.top_k?.find((sp) => sp.code === code)
                  const score = detection?.score || 0

                  return (
                    <td
                      key={`${idx}-${code}`}
                      className={`px-3 py-3 text-center border-l border-[#171717] ${
                        selectedSpecies === code ? 'bg-blue-900 bg-opacity-30' : ''
                      }`}
                    >
                      {score > 0 ? (
                        <div
                          className={`inline-block px-2 py-1 rounded-none text-xs font-semibold ${
                            score > 0.8
                              ? 'bg-[#d9f4d2] text-[#171717]'
                              : score > 0.6
                              ? 'bg-[#f4c542] text-[#171717]'
                              : 'bg-[#f4c542] text-[#171717]'
                          }`}
                        >
                          {(score * 100).toFixed(0)}%
                        </div>
                      ) : (
                        <span className="text-[#8a806f]">-</span>
                      )}
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
      </table>

      <p className="text-[#766d5e] text-xs mt-4">
        Showing top {speciesList.length} species. Each window is 5 seconds.
      </p>
    </div>
  )
}
