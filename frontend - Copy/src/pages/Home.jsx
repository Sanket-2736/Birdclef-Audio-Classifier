import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'

export default function Home() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-navy-900 text-white overflow-hidden">
      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center"
        >
          <h1 className="text-5xl sm:text-7xl font-bold mb-6 bg-gradient-to-r from-blue-400 via-blue-500 to-cyan-400 bg-clip-text text-transparent">
            Identify Birds by Sound
          </h1>
          <p className="text-xl sm:text-2xl text-navy-300 mb-12 max-w-3xl mx-auto">
            Advanced AI-powered audio classification for bird species detection. Used in the BirdCLEF 2024 competition.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-6 justify-center mb-16">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/how-it-works')}
              className="px-8 py-4 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold text-lg transition"
            >
              Try the Demo
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/about')}
              className="px-8 py-4 bg-navy-800 border border-navy-600 hover:border-blue-500 rounded-lg font-semibold text-lg transition"
            >
              Learn More
            </motion.button>
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="bg-navy-800 bg-opacity-50 border-y border-navy-700 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold text-center mb-16">Why BirdCLEF?</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: '🎯',
                title: 'Accurate Detection',
                description: 'Multi-stage ensemble combining Perch embeddings, ProtoSSM, MLP, Residual refinement, and SED detection.'
              },
              {
                icon: '🏆',
                title: 'Competition-Grade',
                description: 'Developed for the BirdCLEF 2024 challenge with real-world training on 10,000+ bird species recordings.'
              },
              {
                icon: '⚡',
                title: 'Fast & Efficient',
                description: '60-second audio processed in 12 overlapping windows with optimized ONNX inference.'
              }
            ].map((feature, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.2 }}
                viewport={{ once: true }}
                className="bg-navy-900 border border-navy-600 rounded-lg p-8 hover:border-blue-500 transition"
              >
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                <p className="text-navy-300">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Preview */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <h2 className="text-4xl font-bold mb-12 text-center">The Pipeline</h2>

        <div className="bg-navy-800 border border-navy-600 rounded-lg p-8 mb-8">
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center font-bold">1</div>
              <div>
                <h3 className="font-semibold text-lg">Audio Preprocessing</h3>
                <p className="text-navy-300">Normalize to 32 kHz, split into 12 overlapping 5-second windows</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center font-bold">2</div>
              <div>
                <h3 className="font-semibold text-lg">Multi-Branch Detection</h3>
                <p className="text-navy-300">Perch embeddings + ProtoSSM + MLP + Residual correction + SED ensemble</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center font-bold">3</div>
              <div>
                <h3 className="font-semibold text-lg">Rank-Aware Blending</h3>
                <p className="text-navy-300">Blend scores (0.6 Proto + 0.4 SED), apply thresholds, smooth over time</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center font-bold">4</div>
              <div>
                <h3 className="font-semibold text-lg">Results</h3>
                <p className="text-navy-300">Per-window and aggregate species predictions with confidence scores</p>
              </div>
            </div>
          </div>
        </div>

        <div className="text-center">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate('/how-it-works')}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition"
          >
            Explore Interactive Pipeline →
          </motion.button>
        </div>
      </section>

      {/* Sample Result Preview */}
      <section className="bg-navy-800 bg-opacity-50 border-y border-navy-700 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold mb-12 text-center">Sample Results</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-navy-900 border border-navy-600 rounded-lg p-8">
              <h3 className="text-xl font-semibold mb-4">Top Detected Species</h3>
              <div className="space-y-3">
                {[
                  { name: 'American Crow', score: 0.92, windows: 10 },
                  { name: 'Blue Jay', score: 0.95, windows: 8 },
                  { name: 'Carolina Wren', score: 0.91, windows: 7 }
                ].map((sp, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className="text-navy-300">{sp.name}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-navy-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-blue-500 to-blue-400"
                          style={{ width: `${sp.score * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-semibold w-12">{(sp.score * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-navy-900 border border-navy-600 rounded-lg p-8">
              <h3 className="text-xl font-semibold mb-4">Recording Details</h3>
              <div className="space-y-2 text-sm text-navy-300">
                <p><span className="font-semibold">Duration:</span> 60 seconds</p>
                <p><span className="font-semibold">Sample Rate:</span> 32 kHz</p>
                <p><span className="font-semibold">Windows:</span> 12 × 5 seconds</p>
                <p><span className="font-semibold">Location:</span> New York, USA</p>
                <p><span className="font-semibold">Time:</span> 2:30 PM</p>
              </div>
            </div>
          </div>

          <div className="text-center mt-8">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/how-it-works')}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition"
            >
              View Full Demo →
            </motion.button>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <h2 className="text-4xl font-bold mb-6">Ready to Explore?</h2>
        <p className="text-xl text-navy-300 mb-8 max-w-2xl mx-auto">
          Walk through the interactive pipeline, experiment with parameters, and see how bird species are classified.
        </p>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => navigate('/how-it-works')}
          className="px-8 py-4 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold text-lg transition"
        >
          Take the Interactive Tour
        </motion.button>
      </section>
    </div>
  )
}
