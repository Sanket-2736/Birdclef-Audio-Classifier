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
    <div className="bg-white rounded-none-none p-6 border-2 border-[#171717] shadow-[5px_5px_0_#171717] mb-8">
      <h2 className="text-2xl font-black tracking-tight text-[#171717] mb-6">Top Species Detected</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {topSpecies.map((species) => {
          const info = speciesInfo[species.code] || {}
          const isFeedback = feedback?.[species.code]
          const isSelected = selectedSpecies === species.code

          return (
            <div
              key={species.code}
              onClick={() => onSelect?.(species.code)}
              className={`bg-[#fff3d6] rounded-none-none p-6 border-2 cursor-pointer border-2 border-[#171717] shadow-[4px_4px_0_#171717] transition-all hover:-translate-y-0.5 ${
                isSelected ? 'border-[#171717] bg-white' : 'border-[#171717] hover:border-[#171717]'
              }`}
            >
              {/* Header */}
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">
                      {taxonIcons[species.taxon] || '🦜'}
                    </span>
                    <h3 className="text-xl font-semibold text-[#171717]">
                      {info.common_name || species.common_name}
                    </h3>
                  </div>
                  <p className="text-[#766d5e] text-sm">
                    <em>{info.scientific_name || species.scientific_name}</em>
                  </p>
                  {species.taxon && (
                    <div className="inline-block mt-2 px-2 py-1 bg-[#f4ead4] rounded-none text-xs text-[#514a40]">
                      {species.taxon}
                    </div>
                  )}
                </div>
                <div className="text-right ml-4">
                  <div className="text-3xl font-bold text-[#171717]">
                    {(species.max_score * 100).toFixed(0)}%
                  </div>
                  <p className="text-[#766d5e] text-xs">max confidence</p>
                </div>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div>
                  <p className="text-[#766d5e] text-xs">Detected in</p>
                  <p className="text-lg font-semibold text-[#171717]">
                    {species.windows_detected}
                  </p>
                  <p className="text-[#766d5e] text-xs">windows</p>
                </div>
                <div>
                  <p className="text-[#766d5e] text-xs">Duration</p>
                  <p className="text-lg font-semibold text-[#171717]">
                    {species.seconds_present?.toFixed(1) || 'N/A'}
                  </p>
                  <p className="text-[#766d5e] text-xs">seconds</p>
                </div>
                <div>
                  <p className="text-[#766d5e] text-xs">Mean</p>
                  <p className="text-lg font-semibold text-[#171717]">
                    {(species.mean_score * 100).toFixed(0)}%
                  </p>
                </div>
              </div>

              {/* Progress bar */}
              <div className="mb-4 bg-[#f4ead4] rounded-none-full h-2 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-blue-500 to-blue-400 h-2 transition-all"
                  style={{ width: `${species.max_score * 100}%` }}
                />
              </div>

              {/* Feedback buttons */}
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => handleFeedback(species.code, true)}
                  className={`flex-1 py-2 px-3 rounded-none text-sm font-bold border-2 border-[#171717] shadow-[3px_3px_0_#171717] transition hover:translate-x-[1px] hover:translate-y-[1px] ${
                    isFeedback === true
                      ? 'bg-[#d9f4d2] text-[#171717]'
                      : 'bg-[#f4ead4] text-[#514a40] hover:bg-[#eadfc9]'
                  }`}
                >
                  👍 Correct
                </button>
                <button
                  onClick={() => handleFeedback(species.code, false)}
                  className={`flex-1 py-2 px-3 rounded-none text-sm font-bold border-2 border-[#171717] shadow-[3px_3px_0_#171717] transition hover:translate-x-[1px] hover:translate-y-[1px] ${
                    isFeedback === false
                      ? 'bg-[#ffcfdb] text-[#171717]'
                      : 'bg-[#f4ead4] text-[#514a40] hover:bg-[#eadfc9]'
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
                className="text-sm text-[#171717] hover:text-[#171717] font-medium"
              >
                {expandedInfo === species.code ? '▼ Hide info' : '▶ Species info'}
              </button>

              {expandedInfo === species.code && (
                <div className="mt-4 pt-4 border-t border-[#171717] text-sm text-[#514a40] space-y-2">
                  {info.scientific_name && (
                    <p>
                      <strong>Scientific:</strong> <em>{info.scientific_name}</em>
                    </p>
                  )}
                  {info.taxon && (
                    <p>
                      <strong>Taxon:</strong> {info.taxon}
                    </p>
                  )}
                  {species.code && (
                    <p>
                      <strong>Code:</strong> <code className="text-xs font-mono bg-[#f4ead4] px-1 py-0.5">{species.code}</code>
                    </p>
                  )}
                  <div className="flex gap-2 pt-2">
                    {info.wikipedia_url && (
                      <a
                        href={info.wikipedia_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#4b9fc9] hover:text-[#2a7aa8] underline"
                      >
                        📚 Wikipedia
                      </a>
                    )}
                    {info.xeno_canto_search && (
                      <a
                        href={info.xeno_canto_search}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#4b9fc9] hover:text-[#2a7aa8] underline"
                      >
                        🔊 Xeno-canto
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
