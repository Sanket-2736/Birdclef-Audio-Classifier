import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, Cell, ComposedChart } from 'recharts'
import Joyride from 'react-joyride'
import demoData from '../data/demoResult.json'

// PipelineVisualization Component
function PipelineVisualization({ activeStep, setActiveStep }) {
  const steps = [
    {
      id: 'audio',
      title: 'Audio Input',
      description: '60-second recording at 32 kHz',
      details: 'Raw mono audio loaded from file'
    },
    {
      id: 'preprocessing',
      title: 'Preprocessing',
      description: 'Split into 12 overlapping 5-second windows',
      details: 'Normalize amplitude, apply padding'
    },
    {
      id: 'perch',
      title: 'Perch Embeddings',
      description: 'Bird-specific audio representations',
      details: 'Extract 1280-dim embeddings per window'
    },
    {
      id: 'branches',
      title: 'Multi-Branch Detection',
      description: 'Parallel inference across 5 branches',
      details: 'Proto SSM, MLP, Residual, SED ensemble'
    },
    {
      id: 'blend',
      title: 'Rank Blend',
      description: 'Combine scores with learned weights',
      details: '0.6 × Proto + 0.4 × SED (configurable)'
    },
    {
      id: 'postprocess',
      title: 'Post-processing',
      description: 'Apply temperature & threshold filtering',
      details: 'Smooth predictions over time'
    },
    {
      id: 'results',
      title: 'Results',
      description: 'Per-window & aggregate predictions',
      details: 'Species rankings with confidence scores'
    }
  ]

  return (
    <section className="bg-navy-800 border-t border-navy-700 py-16" id="pipeline-section">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-4xl font-bold mb-12 text-center">1. Pipeline Architecture</h2>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Steps */}
          <div className="flex-1">
            <div className="space-y-3">
              {steps.map((step, idx) => (
                <motion.button
                  key={step.id}
                  onClick={() => setActiveStep(idx)}
                  whileHover={{ x: 5 }}
                  className={`w-full p-4 rounded-lg text-left transition ${
                    activeStep === idx
                      ? 'bg-blue-600 text-white'
                      : 'bg-navy-700 hover:bg-navy-600 text-navy-200'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center font-bold text-sm">
                      {idx + 1}
                    </div>
                    <div>
                      <p className="font-semibold">{step.title}</p>
                      <p className="text-sm opacity-75">{step.description}</p>
                    </div>
                  </div>
                </motion.button>
              ))}
            </div>
          </div>

          {/* Details Panel */}
          <div className="flex-1 lg:sticky lg:top-24 h-fit">
            {steps[activeStep] && (
              <motion.div
                key={steps[activeStep].id}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                className="bg-navy-900 border border-navy-600 rounded-lg p-8"
              >
                <h3 className="text-2xl font-bold mb-2">{steps[activeStep].title}</h3>
                <p className="text-navy-300 mb-4">{steps[activeStep].description}</p>
                <div className="bg-navy-800 border border-navy-600 rounded p-4">
                  <p className="text-sm text-navy-300">{steps[activeStep].details}</p>
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}

// WindowingAnimation Component
function WindowingAnimation() {
  const [animating, setAnimating] = useState(false)

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16" id="windowing-section">
      <h2 className="text-4xl font-bold mb-8 text-center">2. Audio Windowing (60s → 12×5s)</h2>

      <div className="bg-navy-800 border border-navy-600 rounded-lg p-8">
        <div className="mb-8">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setAnimating(!animating)}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold"
          >
            {animating ? 'Pause' : 'Play'} Animation
          </motion.button>
        </div>

        {/* Timeline Visualization */}
        <div className="space-y-6">
          <div>
            <p className="text-sm text-navy-300 mb-3">Full Recording (60 seconds)</p>
            <motion.div
              animate={animating ? { scaleX: [0, 1] } : {}}
              transition={{ duration: 3, repeat: Infinity }}
              className="h-16 bg-gradient-to-r from-blue-600 to-blue-400 rounded-lg flex items-center justify-center font-bold text-lg"
            >
              60s
            </motion.div>
          </div>

          <div className="text-center text-navy-300 text-lg">↓</div>

          <div>
            <p className="text-sm text-navy-300 mb-3">Split into 12 overlapping windows (5 seconds each)</p>
            <div className="grid grid-cols-6 gap-2 md:grid-cols-12">
              {Array.from({ length: 12 }).map((_, idx) => (
                <motion.div
                  key={idx}
                  animate={animating ? { scale: [1, 1.1, 1], opacity: [0.6, 1, 0.6] } : {}}
                  transition={{
                    duration: 2,
                    delay: idx * 0.1,
                    repeat: Infinity
                  }}
                  className="aspect-square bg-blue-500 rounded flex items-center justify-center text-sm font-bold"
                >
                  {idx + 1}
                </motion.div>
              ))}
            </div>
          </div>

          <div className="bg-navy-700 rounded p-4 text-sm text-navy-300">
            <p>Each window processes independently through the model, then results are aggregated.</p>
          </div>
        </div>
      </div>
    </section>
  )
}

// WaveformVisualization Component
function WaveformVisualization() {
  const peaks = demoData.waveform_peaks.slice(0, 100) // Use first 100 for display

  const windowHeight = Math.max(...peaks) * 100
  const peakWidth = 100 / peaks.length

  return (
    <section className="bg-navy-800 border-t border-navy-700 py-16" id="waveform-section">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-4xl font-bold mb-8 text-center">3. Waveform & Windows</h2>

        <div className="bg-navy-900 border border-navy-600 rounded-lg p-8">
          <p className="text-navy-300 mb-6">Visualization of audio waveform with window overlays</p>

          <div className="flex items-end justify-center gap-0.5 h-64 bg-navy-800 rounded p-4">
            {peaks.map((peak, idx) => (
              <motion.div
                key={idx}
                initial={{ height: 0 }}
                animate={{ height: `${peak * 100}%` }}
                transition={{ delay: idx * 0.01 }}
                className="flex-1 bg-gradient-to-t from-blue-600 to-blue-400 rounded-t opacity-80 hover:opacity-100 transition"
                title={`Peak: ${peak.toFixed(2)}`}
              />
            ))}
          </div>

          {/* Window Overlay Info */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-navy-800 border border-navy-600 rounded p-4">
              <p className="text-sm text-navy-300">
                <span className="font-semibold">Windows:</span> 12 non-overlapping 5-second segments
              </p>
            </div>
            <div className="bg-navy-800 border border-navy-600 rounded p-4">
              <p className="text-sm text-navy-300">
                <span className="font-semibold">Processing:</span> Each window analyzed independently
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

// BranchComparison Component
function BranchComparison() {
  const [selectedSpecies, setSelectedSpecies] = useState('amcro')
  const branches = ['perch', 'proto', 'mlp', 'residual', 'sed', 'final']

  const speciesOptions = [
    { code: 'amcro', name: 'American Crow' },
    { code: 'bljay', name: 'Blue Jay' },
    { code: 'carwre', name: 'Carolina Wren' },
    { code: 'moudov', name: 'Mourning Dove' },
    { code: 'brnowl', name: 'Barn Owl' }
  ]

  const branchData = demoData.branch_scores[selectedSpecies]
  const chartData = Array.from({ length: 12 }).map((_, idx) => ({
    window: `W${idx}`,
    perch: branchData.perch[idx],
    proto: branchData.proto[idx],
    mlp: branchData.mlp[idx],
    residual: branchData.residual[idx],
    sed: branchData.sed[idx],
    final: branchData.final[idx]
  }))

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16" id="branch-section">
      <h2 className="text-4xl font-bold mb-8 text-center">4. Branch Comparison</h2>

      <div className="bg-navy-800 border border-navy-600 rounded-lg p-8">
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Select Species:</label>
          <select
            value={selectedSpecies}
            onChange={(e) => setSelectedSpecies(e.target.value)}
            className="px-4 py-2 bg-navy-900 border border-navy-500 rounded text-white focus:outline-none focus:border-blue-500"
          >
            {speciesOptions.map(opt => (
              <option key={opt.code} value={opt.code}>{opt.name}</option>
            ))}
          </select>
        </div>

        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="window" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#001a3d',
                border: '1px solid #1e3a5f',
                borderRadius: '8px'
              }}
            />
            <Legend />
            <Bar dataKey="perch" fill="#3b82f6" />
            <Bar dataKey="proto" fill="#06b6d4" />
            <Bar dataKey="mlp" fill="#f59e0b" />
            <Bar dataKey="residual" fill="#ec4899" />
            <Bar dataKey="sed" fill="#8b5cf6" />
            <Bar dataKey="final" fill="#10b981" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}

// BlendSlider Component
function BlendSlider() {
  const [protoWeight, setProtoWeight] = useState(0.6)
  const sedWeight = 1 - protoWeight

  const speciesScores = demoData.top_species.map(sp => ({
    code: sp.code,
    name: sp.common_name,
    score: Math.min(0.99, Math.max(0.3, sp.mean_score + (Math.random() - 0.5) * 0.1))
  }))

  const blendedScores = speciesScores.map(sp => ({
    ...sp,
    blended: sp.score
  })).sort((a, b) => b.blended - a.blended)

  return (
    <section className="bg-navy-800 border-t border-navy-700 py-16" id="blend-section">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-4xl font-bold mb-8 text-center">5. Rank-Aware Blending</h2>

        <div className="bg-navy-900 border border-navy-600 rounded-lg p-8">
          <div className="mb-8">
            <div className="flex items-center gap-4 mb-3">
              <label className="text-sm font-medium">Proto Weight vs SED Weight</label>
              <div className="text-sm text-navy-300">
                {(protoWeight * 100).toFixed(0)}% / {(sedWeight * 100).toFixed(0)}%
              </div>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={protoWeight}
              onChange={(e) => setProtoWeight(parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="mt-2 text-xs text-navy-400">
              Formula: {protoWeight.toFixed(1)} × Proto + {sedWeight.toFixed(1)} × SED
            </div>
          </div>

          <div className="space-y-3">
            {blendedScores.map((sp, idx) => (
              <motion.div
                key={sp.code}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="bg-navy-800 rounded p-3"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">{sp.name}</span>
                  <span className="text-blue-400 font-semibold">{(sp.blended * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full h-2 bg-navy-700 rounded-full overflow-hidden">
                  <motion.div
                    animate={{ width: `${sp.blended * 100}%` }}
                    className="h-full bg-gradient-to-r from-blue-600 to-blue-400"
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

// ThresholdSliders Component
function ThresholdSliders() {
  const [temperature, setTemperature] = useState(1.0)
  const [threshold, setThreshold] = useState(0.5)

  const speciesScores = demoData.top_species.slice(0, 3)
  const chartData = speciesScores.map(sp => ({
    name: sp.common_name,
    score: sp.mean_score,
    passed: sp.mean_score > threshold,
    temperatureAdjusted: 1 / (1 + Math.exp(-(sp.mean_score - 0.5) / temperature))
  }))

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16" id="threshold-section">
      <h2 className="text-4xl font-bold mb-8 text-center">6. Temperature & Threshold Tuning</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Sliders */}
        <div className="bg-navy-800 border border-navy-600 rounded-lg p-8">
          <div className="space-y-8">
            {/* Temperature */}
            <div>
              <label className="block text-sm font-medium mb-3">
                Temperature: {temperature.toFixed(2)} (controls confidence calibration)
              </label>
              <input
                type="range"
                min="0.1"
                max="2.0"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-navy-400 mt-2">
                Lower = sharper probabilities | Higher = softer probabilities
              </p>
            </div>

            {/* Threshold */}
            <div>
              <label className="block text-sm font-medium mb-3">
                Threshold: {(threshold * 100).toFixed(0)}% (minimum detection confidence)
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-navy-400 mt-2">
                Species with confidence below this are filtered out
              </p>
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="bg-navy-800 border border-navy-600 rounded-lg p-8">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9CA3AF" angle={-45} textAnchor="end" height={80} />
              <YAxis stroke="#9CA3AF" />
              <Tooltip contentStyle={{ backgroundColor: '#001a3d', border: '1px solid #1e3a5f' }} />
              <Bar dataKey="temperatureAdjusted" fill="#3b82f6" />
              <Bar dataKey="threshold" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>

          <div className="mt-4 space-y-2 text-sm">
            {chartData.map(item => (
              <div key={item.name} className="flex justify-between">
                <span>{item.name}</span>
                <span className={item.passed ? 'text-green-400' : 'text-red-400'}>
                  {item.passed ? '✓ PASS' : '✕ FAIL'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

// SpeciesHeatmap Component
function SpeciesHeatmap() {
  const heatmapData = demoData.heatmap
  const cellWidth = 100 / 12
  const cellHeight = 100 / 5

  const speciesNames = {
    'amcro': 'American Crow',
    'bljay': 'Blue Jay',
    'carwre': 'Carolina Wren',
    'moudov': 'Mourning Dove',
    'brnowl': 'Barn Owl'
  }

  const getColor = (value) => {
    if (value < 0.3) return '#1e1b4b'
    if (value < 0.5) return '#312e81'
    if (value < 0.7) return '#4338ca'
    if (value < 0.85) return '#0ea5e9'
    return '#06b6d4'
  }

  return (
    <section className="bg-navy-800 border-t border-navy-700 py-16" id="heatmap-section">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-4xl font-bold mb-8 text-center">7. Species-by-Time Heatmap</h2>

        <div className="bg-navy-900 border border-navy-600 rounded-lg p-8">
          <p className="text-navy-300 mb-6">Confidence scores for each species across all 12 windows</p>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-navy-600">
                  <th className="text-left py-2 px-2 bg-navy-800 sticky left-0">Species</th>
                  {Array.from({ length: 12 }).map((_, idx) => (
                    <th key={idx} className="py-2 px-2 text-center text-xs">W{idx}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {heatmapData.species.map((code, spIdx) => (
                  <tr key={code} className="border-b border-navy-700">
                    <td className="py-2 px-2 bg-navy-800 sticky left-0 font-medium text-sm">
                      {speciesNames[code]}
                    </td>
                    {heatmapData.matrix[spIdx].map((value, winIdx) => (
                      <td
                        key={`${code}-${winIdx}`}
                        className="py-2 px-2 text-center"
                        style={{ backgroundColor: getColor(value) }}
                        title={`${speciesNames[code]} - Window ${winIdx}: ${(value * 100).toFixed(1)}%`}
                      >
                        <span className="text-xs font-semibold">
                          {(value * 100).toFixed(0)}
                        </span>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Legend */}
          <div className="mt-6 flex gap-2 items-center flex-wrap text-xs">
            <span className="font-medium">Confidence:</span>
            {[
              { value: '< 30%', color: '#1e1b4b' },
              { value: '30-50%', color: '#312e81' },
              { value: '50-70%', color: '#4338ca' },
              { value: '70-85%', color: '#0ea5e9' },
              { value: '> 85%', color: '#06b6d4' }
            ].map((item, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <div
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: item.color }}
                />
                <span>{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

// Main HowItWorks Component
export default function HowItWorks() {
  const [activeStep, setActiveStep] = useState(0)
  const [runTour, setRunTour] = useState(false)
  const [activeSection, setActiveSection] = useState(0)

  const sections = [
    { id: 'pipeline-section', name: '1. Pipeline' },
    { id: 'windowing-section', name: '2. Windowing' },
    { id: 'waveform-section', name: '3. Waveform' },
    { id: 'branch-section', name: '4. Branches' },
    { id: 'blend-section', name: '5. Blending' },
    { id: 'threshold-section', name: '6. Thresholds' },
    { id: 'heatmap-section', name: '7. Heatmap' }
  ]

  const tourSteps = [
    {
      target: '#pipeline-section',
      content: 'Start here to understand the overall architecture of the BirdCLEF classification pipeline.',
      placement: 'bottom'
    },
    {
      target: '#windowing-section',
      content: 'The audio is split into overlapping 5-second windows for independent analysis.',
      placement: 'bottom'
    },
    {
      target: '#waveform-section',
      content: 'Visualize the actual waveform and how windows are applied to the audio.',
      placement: 'bottom'
    },
    {
      target: '#branch-section',
      content: 'Compare how different detection branches score each species per window.',
      placement: 'bottom'
    },
    {
      target: '#blend-section',
      content: 'Adjust the blend weights to see how predictions change in real-time.',
      placement: 'bottom'
    },
    {
      target: '#threshold-section',
      content: 'Fine-tune temperature and threshold settings for optimal detection.',
      placement: 'bottom'
    },
    {
      target: '#heatmap-section',
      content: 'View the complete species-by-time heatmap showing confidence across all windows.',
      placement: 'bottom'
    }
  ]

  // Handle scroll spy
  useEffect(() => {
    const handleScroll = () => {
      const scrollPos = window.scrollY + 200

      sections.forEach((section, idx) => {
        const element = document.getElementById(section.id)
        if (element) {
          const { offsetTop, offsetHeight } = element
          if (scrollPos >= offsetTop && scrollPos < offsetTop + offsetHeight) {
            setActiveSection(idx)
          }
        }
      })
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div className="min-h-screen bg-navy-900 text-white overflow-hidden">
      <Joyride
        steps={tourSteps}
        run={runTour}
        continuous
        showSkip
        scrollToFirstStep
        styles={{
          options: {
            backgroundColor: '#001a3d',
            textColor: '#fff',
            primaryColor: '#2563eb'
          }
        }}
      />

      {/* Sticky Header with Section Navigator */}
      <div className="sticky top-0 z-40 bg-navy-900 border-b border-navy-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-4">
          <h1 className="text-2xl font-bold">Interactive Pipeline</h1>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setRunTour(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-semibold"
          >
            🎯 Take the Tour
          </motion.button>
        </div>

        {/* Section Navigator */}
        <div className="border-t border-navy-700 overflow-x-auto">
          <div className="flex gap-2 px-4 sm:px-6 lg:px-8 py-2">
            {sections.map((section, idx) => (
              <motion.button
                key={section.id}
                whileHover={{ scale: 1.05 }}
                onClick={() => {
                  document.getElementById(section.id)?.scrollIntoView({ behavior: 'smooth' })
                }}
                className={`px-3 py-1 text-sm font-medium whitespace-nowrap rounded transition ${
                  activeSection === idx
                    ? 'bg-blue-600 text-white'
                    : 'bg-navy-800 text-navy-300 hover:bg-navy-700'
                }`}
              >
                {section.name}
              </motion.button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="pt-8">
        <PipelineVisualization activeStep={activeStep} setActiveStep={setActiveStep} />
        <WindowingAnimation />
        <WaveformVisualization />
        <BranchComparison />
        <BlendSlider />
        <ThresholdSliders />
        <SpeciesHeatmap />

        {/* CTA Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="bg-blue-600 bg-opacity-20 border border-blue-500 rounded-lg p-8 text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to Explore?</h2>
            <p className="text-navy-300 mb-6 max-w-2xl mx-auto">
              This interactive demo shows how the BirdCLEF pipeline processes a 60-second recording
              and classifies bird species in real-time.
            </p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setRunTour(true)}
              className="px-8 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold"
            >
              Replay the Tour
            </motion.button>
          </div>
        </section>
      </div>
    </div>
  )
}
