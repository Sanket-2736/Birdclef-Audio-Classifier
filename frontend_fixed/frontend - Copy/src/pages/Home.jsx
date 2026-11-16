import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'

export default function Home() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-[#fff8e8] text-[#171717] overflow-hidden">
      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center"
        >
          <div className="inline-flex items-center gap-2 border-2 border-black bg-[#b9e7ff] px-3 py-1.5 shadow-[3px_3px_0_#171717] mb-7">
            <span className="h-2 w-2 rounded-full bg-[#171717]" />
            <span className="font-mono text-xs font-bold uppercase tracking-widest">WildEcho / Bird Audio Intelligence</span>
          </div>
          <h1 className="text-5xl sm:text-7xl lg:text-8xl font-extrabold tracking-tight mb-6 leading-[0.98]">
            Identify Birds
            <br />
            <span className="bg-[#f4c542] px-2 box-decoration-clone">by Sound.</span>
          </h1>
          <p className="text-lg sm:text-2xl text-[#625d53] mb-12 max-w-3xl mx-auto leading-relaxed">
            Advanced AI-powered audio classification for bird species detection. Used in the BirdCLEF 2026 competition.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-5 justify-center mb-16">
            <motion.button
              whileHover={{ y: -3, x: -2 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => navigate('/how-it-works')}
              className="px-8 py-4 bg-[#f4c542] border-2 border-black shadow-[5px_5px_0_#171717] hover:shadow-[2px_2px_0_#171717] hover:translate-x-[3px] hover:translate-y-[3px] font-extrabold text-lg uppercase tracking-wide transition"
            >
              Try the Demo
            </motion.button>
            <motion.button
              whileHover={{ y: -3, x: -2 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => navigate('/about')}
              className="px-8 py-4 bg-white border-2 border-black shadow-[5px_5px_0_#171717] hover:shadow-[2px_2px_0_#171717] hover:translate-x-[3px] hover:translate-y-[3px] font-extrabold text-lg uppercase tracking-wide transition"
            >
              Learn More
            </motion.button>
          </div>
          <div className="flex flex-wrap justify-center gap-3">
            <span className="border-2 border-black bg-[#d9f4d2] px-3 py-1.5 font-mono text-xs font-bold uppercase">234 Species</span>
            <span className="border-2 border-black bg-[#ffcfdb] px-3 py-1.5 font-mono text-xs font-bold uppercase">AI-Powered Detection</span>
            <span className="border-2 border-black bg-white px-3 py-1.5 font-mono text-xs font-bold uppercase">ONNX Inference</span>
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="bg-[#f4eddd] border-y-2 border-black py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <span className="font-mono text-xs font-bold uppercase tracking-[0.25em] text-[#777168]">Built for field recordings</span>
            <h2 className="text-4xl sm:text-5xl font-extrabold mt-3">Why BirdCLEF?</h2>
          </div>

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
                description: 'Developed for the BirdCLEF 2026 challenge with real-world training on field recordings of 234 species.'
              },
              {
                icon: '⚡',
                title: 'Fast & Efficient',
                description: '60-second audio processed in 12 consecutive windows with optimized ONNX inference.'
              }
            ].map((feature, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.2 }}
                viewport={{ once: true }}
                className={`border-2 border-black p-8 shadow-[6px_6px_0_#171717] hover:-translate-y-1 transition-transform ${
                  idx === 0 ? 'bg-[#b9e7ff]' : idx === 1 ? 'bg-[#ffcfdb]' : 'bg-[#d9f4d2]'
                }`}
              >
                <div className="text-5xl mb-5">{feature.icon}</div>
                <h3 className="text-xl font-extrabold mb-3">{feature.title}</h3>
                <p className="text-[#45413a] leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Preview */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-12">
          <span className="font-mono text-xs font-bold uppercase tracking-[0.25em] text-[#777168]">From raw audio to insight</span>
          <h2 className="text-4xl sm:text-5xl font-extrabold mt-3">The Pipeline</h2>
        </div>

        <div className="bg-white border-2 border-black p-6 sm:p-9 mb-8 shadow-[7px_7px_0_#171717]">
          <div className="space-y-0">
            <div className="flex items-start gap-4 py-5 border-b-2 border-dashed border-[#c9c1b2]">
              <div className="w-12 h-12 shrink-0 border-2 border-black bg-[#f4c542] flex items-center justify-center font-mono text-xl font-extrabold shadow-[3px_3px_0_#171717]">1</div>
              <div>
                <h3 className="font-extrabold text-lg sm:text-xl mb-1">Audio Preprocessing</h3>
                <p className="text-[#625d53]">Normalize to 32 kHz, split into 12 consecutive 5-second windows</p>
              </div>
            </div>

            <div className="flex items-start gap-4 py-5 border-b-2 border-dashed border-[#c9c1b2]">
              <div className="w-12 h-12 shrink-0 border-2 border-black bg-[#b9e7ff] flex items-center justify-center font-mono text-xl font-extrabold shadow-[3px_3px_0_#171717]">2</div>
              <div>
                <h3 className="font-extrabold text-lg sm:text-xl mb-1">Multi-Branch Detection</h3>
                <p className="text-[#625d53]">Perch embeddings + ProtoSSM + MLP + Residual correction + SED ensemble</p>
              </div>
            </div>

            <div className="flex items-start gap-4 py-5 border-b-2 border-dashed border-[#c9c1b2]">
              <div className="w-12 h-12 shrink-0 border-2 border-black bg-[#ffcfdb] flex items-center justify-center font-mono text-xl font-extrabold shadow-[3px_3px_0_#171717]">3</div>
              <div>
                <h3 className="font-extrabold text-lg sm:text-xl mb-1">Rank-Aware Blending</h3>
                <p className="text-[#625d53]">Blend scores (0.6 Proto + 0.4 SED), apply thresholds, smooth over time</p>
              </div>
            </div>

            <div className="flex items-start gap-4 py-5">
              <div className="w-12 h-12 shrink-0 border-2 border-black bg-[#d9f4d2] flex items-center justify-center font-mono text-xl font-extrabold shadow-[3px_3px_0_#171717]">4</div>
              <div>
                <h3 className="font-extrabold text-lg sm:text-xl mb-1">Results</h3>
                <p className="text-[#625d53]">Per-window and aggregate species predictions with confidence scores</p>
              </div>
            </div>
          </div>
        </div>

        <div className="text-center">
          <motion.button
            whileHover={{ y: -2, x: -2 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate('/how-it-works')}
            className="px-6 py-3 bg-[#b9e7ff] border-2 border-black shadow-[4px_4px_0_#171717] hover:shadow-[2px_2px_0_#171717] hover:translate-x-[2px] hover:translate-y-[2px] font-extrabold uppercase tracking-wide transition"
          >
            Explore Interactive Pipeline →
          </motion.button>
        </div>
      </section>

      {/* Sample Result Preview */}
      <section className="bg-[#f4eddd] border-y-2 border-black py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <span className="font-mono text-xs font-bold uppercase tracking-[0.25em] text-[#777168]">A glimpse at the output</span>
            <h2 className="text-4xl sm:text-5xl font-extrabold mt-3">Sample Results</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white border-2 border-black p-8 shadow-[6px_6px_0_#171717]">
              <h3 className="text-xl font-extrabold mb-6">Top Detected Species</h3>
              <div className="space-y-5">
                {[
                  { name: 'American Crow', score: 0.92, windows: 10 },
                  { name: 'Blue Jay', score: 0.95, windows: 8 },
                  { name: 'Carolina Wren', score: 0.91, windows: 7 }
                ].map((sp, idx) => (
                  <div key={idx}>
                    <div className="flex items-center justify-between gap-3 mb-2">
                      <span className="font-semibold">{sp.name}</span>
                      <span className="font-mono text-sm font-extrabold">{(sp.score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full h-3 bg-[#eee8d9] border-2 border-black overflow-hidden">
                      <div
                        className="h-full bg-[#f4c542] border-r-2 border-black"
                        style={{ width: `${sp.score * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-[#b9e7ff] border-2 border-black p-8 shadow-[6px_6px_0_#171717]">
              <h3 className="text-xl font-extrabold mb-6">Recording Details</h3>
              <div className="space-y-0 text-sm">
                <p className="flex justify-between gap-4 py-3 border-b border-black/30"><span className="font-mono font-bold uppercase text-xs">Duration</span><span className="font-bold">60 seconds</span></p>
                <p className="flex justify-between gap-4 py-3 border-b border-black/30"><span className="font-mono font-bold uppercase text-xs">Sample Rate</span><span className="font-bold">32 kHz</span></p>
                <p className="flex justify-between gap-4 py-3 border-b border-black/30"><span className="font-mono font-bold uppercase text-xs">Windows</span><span className="font-bold">12 × 5 seconds</span></p>
                <p className="flex justify-between gap-4 py-3 border-b border-black/30"><span className="font-mono font-bold uppercase text-xs">Location</span><span className="font-bold">New York, USA</span></p>
                <p className="flex justify-between gap-4 py-3"><span className="font-mono font-bold uppercase text-xs">Time</span><span className="font-bold">2:30 PM</span></p>
              </div>
            </div>
          </div>

          <div className="text-center mt-10">
            <motion.button
              whileHover={{ y: -2, x: -2 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => navigate('/how-it-works')}
              className="px-6 py-3 bg-[#ffcfdb] border-2 border-black shadow-[4px_4px_0_#171717] hover:shadow-[2px_2px_0_#171717] hover:translate-x-[2px] hover:translate-y-[2px] font-extrabold uppercase tracking-wide transition"
            >
              View Full Demo →
            </motion.button>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <div className="max-w-4xl mx-auto bg-[#f4c542] border-2 border-black p-8 sm:p-12 shadow-[8px_8px_0_#171717]">
          <span className="font-mono text-xs font-bold uppercase tracking-[0.25em]">Your next discovery starts here</span>
          <h2 className="text-4xl sm:text-5xl font-extrabold mt-4 mb-6">Ready to Explore?</h2>
          <p className="text-lg sm:text-xl text-[#45413a] mb-8 max-w-2xl mx-auto">
            Walk through the interactive pipeline, experiment with parameters, and see how bird species are classified.
          </p>
          <motion.button
            whileHover={{ y: -3, x: -2 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate('/how-it-works')}
            className="px-8 py-4 bg-white border-2 border-black shadow-[5px_5px_0_#171717] hover:shadow-[2px_2px_0_#171717] hover:translate-x-[3px] hover:translate-y-[3px] font-extrabold text-lg uppercase tracking-wide transition"
          >
            Take the Interactive Tour
          </motion.button>
        </div>
      </section>
    </div>
  )
}
