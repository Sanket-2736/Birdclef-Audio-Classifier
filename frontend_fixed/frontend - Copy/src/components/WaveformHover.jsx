import { useEffect, useRef, useState } from 'react'
import WaveSurfer from 'wavesurfer.js'

const WINDOW_SIZE = 5 // seconds
const COLORS = [
  '#4b9fc9', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899',
  '#06b6d4', '#f97316', '#6366f1', '#84cc16', '#0891b2', '#d946ef',
]

// Get stable color for species code
const getSpeciesColor = (code) => {
  let hash = 0
  for (let i = 0; i < code.length; i++) {
    hash = ((hash << 5) - hash) + code.charCodeAt(i)
    hash = hash & hash
  }
  return COLORS[Math.abs(hash) % COLORS.length]
}

export default function WaveformHover({
  audioUrl,
  waveformPeaks,
  duration,
  prediction,
  onWindowClick,
  onTimeChange,
  selectedSpecies,
}) {
  const containerRef = useRef(null)
  const canvasRef = useRef(null)
  const wavesurfer = useRef(null)
  const mountedRef = useRef(true)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [tooltip, setTooltip] = useState(null)
  const [highlightedWindow, setHighlightedWindow] = useState(null)
  const [audioError, setAudioError] = useState(null)

  // Initialize WaveSurfer
  useEffect(() => {
    if (!containerRef.current) return

    mountedRef.current = true

    try {
      wavesurfer.current = WaveSurfer.create({
        container: containerRef.current,
        waveColor: '#b9e7ff',
        progressColor: '#4b9fc9',
        cursorColor: '#171717',
        barWidth: 2,
        barRadius: 3,
        barGap: 1,
        height: 100,
        normalize: true,
        responsive: true,
        backend: 'WebAudio',
      })

      wavesurfer.current.load(audioUrl)

      wavesurfer.current.on('ready', () => {
        if (mountedRef.current) {
          setCurrentTime(0)
          setAudioError(null)
        }
      })

      wavesurfer.current.on('play', () => {
        if (mountedRef.current) setIsPlaying(true)
      })

      wavesurfer.current.on('pause', () => {
        if (mountedRef.current) setIsPlaying(false)
      })

      wavesurfer.current.on('timeupdate', (time) => {
        if (mountedRef.current) {
          setCurrentTime(time)
          onTimeChange?.(time)
        }
      })

      wavesurfer.current.on('error', (error) => {
        console.error('[WaveformHover] WaveSurfer error:', error)
        if (mountedRef.current) {
          setAudioError(error?.message || 'Failed to load audio')
        }
      })

      wavesurfer.current.on('decode-error', (error) => {
        console.error('[WaveformHover] Audio decode error:', error)
        if (mountedRef.current) {
          setAudioError('Failed to decode audio file')
        }
      })
    } catch (err) {
      console.error('[WaveformHover] Failed to initialize WaveSurfer:', err)
      if (mountedRef.current) {
        setAudioError('Failed to initialize audio player')
      }
    }

    return () => {
      mountedRef.current = false
      wavesurfer.current?.destroy()
    }
  }, [audioUrl, onTimeChange])

  // Draw window overlays on canvas
  useEffect(() => {
    if (!canvasRef.current || !containerRef.current) return

    const canvas = canvasRef.current
    const width = containerRef.current.offsetWidth
    const height = 100

    canvas.width = width
    canvas.height = height

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Clear
    ctx.clearRect(0, 0, width, height)

    const windows = prediction?.windows || []
    const numWindows = Math.ceil(duration / WINDOW_SIZE)

    // Draw window overlays
    for (let i = 0; i < numWindows; i++) {
      const windowStart = i * WINDOW_SIZE
      const windowEnd = Math.min(windowStart + WINDOW_SIZE, duration)
      const x1 = (windowStart / duration) * width
      const x2 = (windowEnd / duration) * width
      const w = x2 - x1

      const window = windows[i]

      // Check if padding
      if (window?.is_padding) {
        // Grey hatching for padding
        ctx.fillStyle = 'rgba(100, 116, 139, 0.2)'
        ctx.fillRect(x1, 0, w, height)

        // Diagonal lines
        ctx.strokeStyle = 'rgba(100, 116, 139, 0.3)'
        ctx.lineWidth = 1
        for (let j = -height; j < width; j += 8) {
          ctx.beginPath()
          ctx.moveTo(j + x1, height)
          ctx.lineTo(j + x1 + height, 0)
          ctx.stroke()
        }
      } else if (window && window.top_k && window.top_k.length > 0) {
        // Color by top species in window
        const topCode = window?.top_k?.[0]?.code
        if (topCode) {
          const color = getSpeciesColor(topCode)
          ctx.fillStyle = color + '33' // 20% opacity
          ctx.fillRect(x1, 0, w, height)

          // Border
          ctx.strokeStyle = color + 'aa'
          ctx.lineWidth = 1
          ctx.strokeRect(x1, 0, w, height)
        }
      }
    }

    // Draw beyond duration as grey-hatched
    if (duration < (numWindows * WINDOW_SIZE)) {
      const x1 = (duration / (numWindows * WINDOW_SIZE)) * width
      ctx.fillStyle = 'rgba(100, 116, 139, 0.15)'
      ctx.fillRect(x1, 0, width - x1, height)

      ctx.strokeStyle = 'rgba(100, 116, 139, 0.3)'
      ctx.lineWidth = 1
      for (let j = 0; j < width; j += 8) {
        ctx.beginPath()
        ctx.moveTo(j + x1, height)
        ctx.lineTo(j + x1 + height, 0)
        ctx.stroke()
      }
    }
  }, [duration, prediction, selectedSpecies])

  // Handle canvas mouse move for tooltip
  const handleCanvasMouseMove = (e) => {
    if (!mountedRef.current) return
    if (!canvasRef.current || !containerRef.current) return

    const rect = canvasRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const relX = x / rect.width
    const t = relX * duration
    const windowIndex = Math.floor(t / WINDOW_SIZE)

    const windows = prediction?.windows || []
    const window = windows[windowIndex]

    if (window && !window.is_padding && window.top_k && window.top_k.length > 0) {
      const top3 = (window.top_k || []).slice(0, 3)
      setTooltip({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
        time: t,
        windowStart: windowIndex * WINDOW_SIZE,
        windowEnd: Math.min((windowIndex + 1) * WINDOW_SIZE, duration),
        species: top3,
      })
      setHighlightedWindow(windowIndex)
    } else {
      setTooltip(null)
      setHighlightedWindow(null)
    }
  }

  const handleCanvasMouseLeave = () => {
    setTooltip(null)
    setHighlightedWindow(null)
  }

  const handleCanvasClick = (e) => {
    if (!mountedRef.current) return
    if (!canvasRef.current) return

    const rect = canvasRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const relX = x / rect.width
    const t = relX * duration
    const windowIndex = Math.floor(t / WINDOW_SIZE)

    wavesurfer.current?.seekTo(relX)
    wavesurfer.current?.play()
    onWindowClick?.(windowIndex)
  }

  // Legend
  const uniqueSpecies = []
  const speciesSeen = new Set();
  (prediction?.windows || []).forEach((w) => {
    if (!w.is_padding && w.top_k && w.top_k.length > 0) {
      const code = w?.top_k?.[0]?.code
      if (code && !speciesSeen.has(code)) {
        speciesSeen.add(code)
        uniqueSpecies.push(code)
      }
    }
  })

  const handlePlayPause = () => {
    if (!mountedRef.current) return

    if (isPlaying) {
      wavesurfer.current?.pause()
    } else {
      wavesurfer.current?.play()
    }
  }

  return (
    <div className="bg-white rounded-none-none p-6 border-2 border-[#171717] shadow-[5px_5px_0_#171717] mb-8">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-black tracking-tight text-[#171717]">Audio Playback</h2>
        <div className="text-sm text-[#766d5e]">
          {currentTime.toFixed(1)}s / {duration.toFixed(1)}s
        </div>
      </div>

      {/* Error message */}
      {audioError && (
        <div className="mb-4 p-3 bg-[#ffcfdb] border-2 border-[#dc2626] rounded-none text-sm text-[#dc2626] font-semibold">
          ⚠ {audioError}
        </div>
      )}

      <div className="mb-4 cursor-pointer" ref={containerRef} />

      {/* Canvas overlay with window regions */}
      <div className="relative -mt-[120px] mb-6">
        <canvas
          ref={canvasRef}
          className="w-full h-[100px] cursor-pointer"
          onMouseMove={handleCanvasMouseMove}
          onMouseLeave={handleCanvasMouseLeave}
          onClick={handleCanvasClick}
        />

        {/* Tooltip */}
        {tooltip && (
          <div
            className="absolute bg-[#fff3d6] border border-[#171717] rounded-none-none p-3 text-sm text-[#302b24] z-50 pointer-events-none"
            style={{
              left: `${tooltip.x}px`,
              top: `${tooltip.y - 120}px`,
            }}
          >
            <div className="font-semibold text-[#171717] mb-2">
              {tooltip.time.toFixed(1)}s ({tooltip.windowStart.toFixed(0)}-{tooltip.windowEnd.toFixed(0)}s)
            </div>
            <div className="space-y-1">
              {tooltip.species.map((sp, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-none"
                    style={{
                      backgroundColor: getSpeciesColor(sp?.code || ''),
                      opacity: 0.8,
                    }}
                  />
                  <span className="text-xs">
                    {sp?.name || sp?.code || 'Unknown'} ({((sp?.score ?? 0) * 100).toFixed(0)}%)
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-sm mb-6">
        {uniqueSpecies.slice(0, 12).map((code) => (
          <div key={code} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-none"
              style={{ backgroundColor: getSpeciesColor(code) }}
            />
            <span className="text-[#514a40]">{code}</span>
          </div>
        ))}
        {uniqueSpecies.length > 12 && (
          <span className="text-[#766d5e]">+{uniqueSpecies.length - 12} more</span>
        )}
      </div>

      {/* Play/Pause */}
      <div className="flex gap-4">
        <button
          onClick={handlePlayPause}
          className="flex-1 py-2 px-4 bg-[#b9e7ff] hover:bg-[#a4dcf7] text-[#171717] rounded-none font-bold border-2 border-[#171717] shadow-[3px_3px_0_#171717] transition hover:translate-x-[1px] hover:translate-y-[1px]"
        >
          {isPlaying ? '⏸ Pause' : '▶ Play'}
        </button>
      </div>
    </div>
  )
}
