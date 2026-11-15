import { useState } from 'react'
import speciesInfo from '../data/species_info.json'

const taxonIcons = {
  Aves: '🐦',
  Amphibia: '🐸',
  Reptilia: '🐍',
  Insecta: '🦗',
  Mammalia: '🦌',
  Osteichthyes: '🐟',
}

export default function TopSpeciesCards({
  topSpecies,
  selectedSpecies,
  onSelect,
  feedback,
  onFeedback,
}) {
  const [expandedInfo, setExpandedInfo] = useState(null)

  const handleFeedback = (code, isCorrect) => {
    onFeedback?.(code, isCorrect)
  }

  return (
    <div className="bg-navy-800 rounded-lg p-6 border border-navy-700 mb-8">
      <h2 className="text-2xl font-bold text-white mb-6">Top Species Detected</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {topSpecies.map((species) => {
          const info = speciesInfo[species.code] || {}
          const isFeedback = feedback?.[species.code]
          const isSelected = selectedSpecies === species.code

          return (
            <div
              key={species.code}
              onClick={() => onSelect?.(species.code)}
              className={`bg-navy-900 rounded-lg p-6 border-2 cursor-pointer transition-all ${
                isSelected ? 'border-blue-500 bg-navy-800' : 'border-navy-600 hover:border-navy-500'
              }`}
            >
              {/* Header */}
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">
                      {taxonIcons[species.taxon] || '🦜'}
                    </span>
                    <h3 className="text-xl font-semibold text-blue-400">
                      {info.common_name || species.common_name}
                    </h3>
                  </div>
                  <p className="text-navy-400 text-sm">
                    <em>{info.scientific_name || species.scientific_name}</em>
                  </p>
                  {species.taxon && (
                    <div className="inline-block mt-2 px-2 py-1 bg-navy-700 rounded text-xs text-navy-300">
                      {species.taxon}
                    </div>
                  )}
                </div>
                <div className="text-right ml-4">
                  <div className="text-3xl font-bold text-white">
                    {(species.max_score * 100).toFixed(0)}%
                  </div>
                  <p className="text-navy-400 text-xs">max confidence</p>
                </div>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div>
                  <p className="text-navy-400 text-xs">Detected in</p>
                  <p className="text-lg font-semibold text-white">
                    {species.windows_detected}
                  </p>
                  <p className="text-navy-400 text-xs">windows</p>
                </div>
                <div>
                  <p className="text-navy-400 text-xs">Duration</p>
                  <p className="text-lg font-semibold text-white">
                    {species.seconds_present?.toFixed(1) || 'N/A'}
                  </p>
                  <p className="text-navy-400 text-xs">seconds</p>
                </div>
                <div>
                  <p className="text-navy-400 text-xs">Mean</p>
                  <p className="text-lg font-semibold text-white">
                    {(species.mean_score * 100).toFixed(0)}%
                  </p>
                </div>
              </div>

              {/* Progress bar */}
              <div className="mb-4 bg-navy-700 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-blue-500 to-blue-400 h-2 transition-all"
                  style={{ width: `${species.max_score * 100}%` }}
                />
              </div>

              {/* Feedback buttons */}
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => handleFeedback(species.code, true)}
                  className={`flex-1 py-2 px-3 rounded text-sm font-medium transition ${
                    isFeedback === true
                      ? 'bg-green-600 text-white'
                      : 'bg-navy-700 text-navy-300 hover:bg-navy-600'
                  }`}
                >
                  👍 Correct
                </button>
                <button
                  onClick={() => handleFeedback(species.code, false)}
                  className={`flex-1 py-2 px-3 rounded text-sm font-medium transition ${
                    isFeedback === false
                      ? 'bg-red-600 text-white'
                      : 'bg-navy-700 text-navy-300 hover:bg-navy-600'
                  }`}
                >
                  👎 Incorrect
                </button>
              </div>

              {/* Expandable info */}
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setExpandedInfo(expandedInfo === species.code ? null : species.code)
                }}
                className="text-sm text-blue-400 hover:text-blue-300 font-medium"
              >
                {expandedInfo === species.code ? '▼ Hide info' : '▶ Species info'}
              </button>

              {expandedInfo === species.code && (
                <div className="mt-4 pt-4 border-t border-navy-700 text-sm text-navy-300 space-y-2">
                  {info.scientific_name && (
                    <p>
                      <strong>Scientific:</strong> {info.scientific_name}
                    </p>
                  )}
                  {info.taxon && (
                    <p>
                      <strong>Taxon:</strong> {info.taxon}
                    </p>
                  )}
                  <div className="flex gap-2 pt-2">
                    {info.wikipedia_url && (
                      <a
                        href={info.wikipedia_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300"
                      >
                        Wikipedia ↗
                      </a>
                    )}
                    {info.xeno_canto_search && (
                      <a
                        href={info.xeno_canto_search}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300"
                      >
                        Xeno-canto ↗
                      </a>
                    )}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
