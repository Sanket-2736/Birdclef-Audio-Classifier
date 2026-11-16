import { useState } from 'react'

export default function HeatmapChart({ prediction, selectedSpecies }) {
  const [hoveredCell, setHoveredCell] = useState(null)

  const windows = prediction?.windows || []
  const validWindows = windows.filter((w) => !w.is_padding)
  const heatmapData = prediction?.heatmap || {}
  const species = heatmapData.species || []
  const matrix = heatmapData.matrix || []

  // Filter species (show top 15)
  const displaySpecies = species.slice(0, 15)
  const displayMatrix = matrix.map((row) => row.slice(0, validWindows.length))

  const getColorForScore = (score) => {
    if (score === 0 || score === null || score === undefined) return '#fff8e8'
    if (score > 0.8) return '#059669'
    if (score > 0.6) return '#d97706'
    if (score > 0.4) return '#f97316'
    if (score > 0.2) return '#dc2626'
    return '#7c3aed'
  }

  const getCellStyle = (rowIdx, colIdx) => {
    const row = displayMatrix[rowIdx] || []
    const score = row[colIdx]
    const color = getColorForScore(score)

    return {
      backgroundColor: color,
      opacity: score > 0 ? 0.8 : 0.4,
    }
  }

  return (
    <div className="bg-white rounded-none-none p-6 border-2 border-[#171717] shadow-[5px_5px_0_#171717] mb-8">
      <h2 className="text-2xl font-black tracking-tight text-[#171717] mb-6">Species × Time Heatmap</h2>

      <div className="overflow-x-auto">
        <div className="flex gap-4">
          {/* Y-axis labels */}
          <div className="flex flex-col justify-start">
            <div className="h-8"></div>
            {displaySpecies.map((spec, idx) => (
              <div
                key={idx}
                className={`h-8 w-32 text-right pr-3 text-xs font-semibold flex items-center justify-end ${
                  selectedSpecies === spec ? 'text-[#171717]' : 'text-[#514a40]'
                }`}
                style={{
                  backgroundColor:
                    selectedSpecies === spec ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
                }}
              >
                {spec.substring(0, 20)}
              </div>
            ))}
          </div>

          {/* Heatmap */}
          <div className="flex flex-col gap-0 border border-[#171717] rounded-none overflow-hidden">
            {/* X-axis (time) */}
            <div className="flex gap-0">
              {validWindows.map((_, colIdx) => {
                const time = colIdx * 5
                return (
                  <div
                    key={`time-${colIdx}`}
                    className="w-12 h-8 flex items-center justify-center text-xs text-[#766d5e] font-semibold border-r border-[#171717] bg-[#fff3d6]"
                  >
                    {time}s
                  </div>
                )
              })}
            </div>

            {/* Cells */}
            {displayMatrix.map((row, rowIdx) => (
              <div key={`row-${rowIdx}`} className="flex gap-0">
                {row.map((score, colIdx) => (
                  <div
                    key={`cell-${rowIdx}-${colIdx}`}
                    className="w-12 h-12 border-r border-b border-[#171717] cursor-pointer hover:opacity-100 transition-opacity"
                    style={getCellStyle(rowIdx, colIdx)}
                    onMouseEnter={() =>
                      score > 0 && setHoveredCell({ rowIdx, colIdx, score })
                    }
                    onMouseLeave={() => setHoveredCell(null)}
                    title={score > 0 ? `${displaySpecies[rowIdx]}: ${(score * 100).toFixed(1)}%` : ''}
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tooltip */}
      {hoveredCell && (
        <div className="mt-4 p-3 bg-[#fff3d6] border border-[#171717] rounded-none text-sm text-[#302b24]">
          <strong>{displaySpecies[hoveredCell.rowIdx]}</strong> at window{' '}
          {hoveredCell.colIdx}: <strong>{(hoveredCell.score * 100).toFixed(1)}%</strong>
        </div>
      )}

      {/* Legend */}
      <div className="mt-6 flex gap-6 flex-wrap">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-none bg-[#d9f4d2] opacity-80"></div>
          <span className="text-sm text-[#514a40]">&gt;80%</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-none bg-[#f4c542] opacity-80"></div>
          <span className="text-sm text-[#514a40]">60-80%</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-none bg-[#f4c542] opacity-80"></div>
          <span className="text-sm text-[#514a40]">40-60%</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-none bg-[#ffcfdb] opacity-80"></div>
          <span className="text-sm text-[#514a40]">20-40%</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-none bg-[#d9d0ff] opacity-80"></div>
          <span className="text-sm text-[#514a40]">&lt;20%</span>
        </div>
      </div>
    </div>
  )
}
