import { useState, useMemo, useRef, useEffect } from 'react'

export default function HeatmapChart({ prediction, selectedSpecies }) {
  const [hoveredCell, setHoveredCell] = useState(null)
  const [scrollLeft, setScrollLeft] = useState(0)
  const containerRef = useRef(null)
  const heatmapContainerRef = useRef(null)

  const windows = prediction?.windows || []
  const validWindows = windows.filter((w) => !w.is_padding)
  const heatmapData = prediction?.heatmap || {}
  const species = heatmapData.species || []
  const matrix = heatmapData.matrix || []

  // Normalize species entries
  const getSpeciesCode = (spec) => {
    if (typeof spec === 'string' || typeof spec === 'number') {
      return String(spec)
    }
    if (spec && typeof spec === 'object') {
      return String(spec.code ?? spec.species_code ?? spec.label ?? spec.name ?? '')
    }
    return ''
  }

  const getSpeciesLabel = (spec) => {
    if (typeof spec === 'string' || typeof spec === 'number') {
      return String(spec)
    }
    if (spec && typeof spec === 'object') {
      return String(spec.common_name ?? spec.name ?? spec.scientific_name ?? spec.code ?? '')
    }
    return ''
  }

  // Filter species (show top 20)
  const displaySpecies = useMemo(() => {
    return Array.isArray(species) ? species.slice(0, 20) : []
  }, [species])

  const displayMatrix = useMemo(() => {
    return Array.isArray(matrix)
      ? matrix
          .slice(0, displaySpecies.length)
          .map((row) => (Array.isArray(row) ? row.slice(0, validWindows.length) : []))
      : []
  }, [matrix, displaySpecies, validWindows])

  // Color function - professional continuous scale
  const getColorForScore = (score) => {
    if (score === null || score === undefined || score === 0) {
      return { bg: '#f8f9fa', text: '#6b7280' } // Light gray for zero
    }

    if (score > 0.85) return { bg: '#065f46', text: '#ffffff' } // Dark green
    if (score > 0.7) return { bg: '#059669', text: '#ffffff' } // Green
    if (score > 0.55) return { bg: '#10b981', text: '#ffffff' } // Light green
    if (score > 0.4) return { bg: '#f59e0b', text: '#ffffff' } // Amber
    if (score > 0.25) return { bg: '#f97316', text: '#ffffff' } // Orange
    if (score > 0.1) return { bg: '#ef4444', text: '#ffffff' } // Red
    return { bg: '#dc2626', text: '#ffffff' } // Dark red
  }

  // Handle horizontal scroll
  const handleScroll = (e) => {
    setScrollLeft(e.target.scrollLeft)
  }

  // Column width calculations
  const CELL_WIDTH = 56 // pixels
  const CELL_HEIGHT = 48 // pixels
  const ROW_LABEL_WIDTH = 200 // pixels
  const totalCellsWidth = validWindows.length * CELL_WIDTH

  return (
    <div className="w-full bg-white rounded-lg border-2 border-gray-200 shadow-md p-6" ref={containerRef}>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Species Detection Timeline</h2>
        <p className="text-sm text-gray-600">
          Shows confidence score for each species across {validWindows.length} time windows
          ({(validWindows.length * 5).toFixed(0)} seconds total)
        </p>
      </div>

      {/* Main Heatmap Container */}
      <div className="mb-6 bg-gray-50 rounded-lg overflow-hidden border border-gray-200">
        <div className="flex">
          {/* Y-axis Labels (Species) */}
          <div className="flex-shrink-0 border-r border-gray-200">
            <div
              className="bg-gray-100 border-b border-gray-200 flex items-center justify-center text-xs font-bold text-gray-600"
              style={{ width: `${ROW_LABEL_WIDTH}px`, height: `${CELL_HEIGHT}px` }}
            >
              Species
            </div>

            {displaySpecies.map((spec, idx) => (
              <div
                key={`species-${idx}`}
                className={`text-xs font-medium px-3 py-2 border-b border-gray-200 flex items-center ${
                  selectedSpecies === getSpeciesCode(spec) ? 'bg-blue-100' : 'bg-white hover:bg-gray-50'
                }`}
                style={{ width: `${ROW_LABEL_WIDTH}px`, height: `${CELL_HEIGHT}px` }}
                title={getSpeciesLabel(spec)}
              >
                <span className="truncate">{getSpeciesLabel(spec)}</span>
              </div>
            ))}
          </div>

          {/* Heatmap Grid */}
          <div className="flex-1 overflow-x-auto" ref={heatmapContainerRef} onScroll={handleScroll}>
            <div>
              {/* X-axis Labels (Time Windows) */}
              <div className="flex bg-gray-100 border-b-2 border-gray-200">
                {validWindows.map((_, colIdx) => {
                  const startTime = colIdx * 5
                  const endTime = (colIdx + 1) * 5
                  return (
                    <div
                      key={`time-${colIdx}`}
                      className="flex-shrink-0 text-xs font-bold text-gray-600 flex items-center justify-center border-r border-gray-200 bg-gray-100"
                      style={{ width: `${CELL_WIDTH}px`, height: `${CELL_HEIGHT}px` }}
                      title={`${startTime}s - ${endTime}s`}
                    >
                      {startTime}s
                    </div>
                  )
                })}
              </div>

              {/* Heatmap Cells */}
              {displayMatrix.map((row, rowIdx) => (
                <div key={`row-${rowIdx}`} className="flex border-b border-gray-200">
                  {row.map((score, colIdx) => {
                    const colors = getColorForScore(score)
                    const speciesCode = getSpeciesCode(displaySpecies[rowIdx])
                    const isSelected = selectedSpecies === speciesCode

                    return (
                      <div
                        key={`cell-${rowIdx}-${colIdx}`}
                        className={`flex-shrink-0 flex items-center justify-center border-r border-gray-200 cursor-pointer transition-all hover:opacity-75 ${
                          isSelected ? 'ring-2 ring-blue-500' : ''
                        }`}
                        style={{
                          width: `${CELL_WIDTH}px`,
                          height: `${CELL_HEIGHT}px`,
                          backgroundColor: colors.bg,
                        }}
                        onMouseEnter={() => {
                          if (score > 0) {
                            setHoveredCell({
                              rowIdx,
                              colIdx,
                              score,
                              species: displaySpecies[rowIdx],
                              time: colIdx * 5,
                            })
                          }
                        }}
                        onMouseLeave={() => setHoveredCell(null)}
                        title={
                          score > 0
                            ? `${getSpeciesLabel(displaySpecies[rowIdx])}: ${(score * 100).toFixed(1)}%`
                            : ''
                        }
                      >
                        {score > 0 && (
                          <span
                            className="text-xs font-bold"
                            style={{ color: colors.text }}
                          >
                            {(score * 100).toFixed(0)}
                          </span>
                        )}
                      </div>
                    )
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Tooltip */}
      {hoveredCell && (
        <div className="fixed bg-white border-2 border-gray-300 rounded-lg p-4 text-sm text-gray-900 z-50 shadow-lg max-w-xs"
          style={{
            left: `${hoveredCell.colIdx * CELL_WIDTH + 250}px`,
            top: `${hoveredCell.rowIdx * CELL_HEIGHT + 150}px`,
          }}
        >
          <div className="font-bold text-gray-900 mb-2">
            {getSpeciesLabel(hoveredCell.species)}
          </div>
          <div className="space-y-1 text-xs text-gray-700">
            <div><strong>Confidence:</strong> {(hoveredCell.score * 100).toFixed(1)}%</div>
            <div><strong>Time Window:</strong> {hoveredCell.time}s - {hoveredCell.time + 5}s</div>
            <div><strong>Species Code:</strong> {getSpeciesCode(hoveredCell.species)}</div>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="mt-6 border-t-2 border-gray-200 pt-6">
        <h3 className="text-sm font-bold text-gray-900 mb-4">Confidence Scale</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-7 gap-3">
          <LegendItem label=">85%" color="#065f46" />
          <LegendItem label="70-85%" color="#059669" />
          <LegendItem label="55-70%" color="#10b981" />
          <LegendItem label="40-55%" color="#f59e0b" />
          <LegendItem label="25-40%" color="#f97316" />
          <LegendItem label="10-25%" color="#ef4444" />
          <LegendItem label="<10%" color="#dc2626" />
        </div>
      </div>

      {/* Stats Footer */}
      <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4 text-center pt-4 border-t border-gray-200">
        <StatCard label="Species" value={displaySpecies.length} />
        <StatCard label="Time Windows" value={validWindows.length} />
        <StatCard label="Duration" value={`${(validWindows.length * 5).toFixed(0)}s`} />
        <StatCard label="Cells" value={displaySpecies.length * validWindows.length} />
      </div>
    </div>
  )
}

function LegendItem({ label, color }) {
  return (
    <div className="flex items-center gap-2">
      <div
        className="w-6 h-6 rounded border border-gray-300 flex-shrink-0"
        style={{ backgroundColor: color }}
      ></div>
      <span className="text-xs text-gray-700">{label}</span>
    </div>
  )
}

function StatCard({ label, value }) {
  return (
    <div>
      <div className="text-xs font-medium text-gray-600">{label}</div>
      <div className="text-xl font-bold text-gray-900">{value}</div>
    </div>
  )
}
