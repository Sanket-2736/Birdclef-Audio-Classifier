import { motion } from 'framer-motion'

const teamConfig = [
  {
    name: 'BirdCLEF Team',
    role: 'Project Lead',
    bio: 'Competition-winning bird species classification system.'
  },
  {
    name: 'Cornell Lab of Ornithology',
    role: 'Data & Expertise',
    bio: 'Curated bird call dataset and domain guidance for model development.'
  },
  {
    name: 'LifeCLEF & Kaggle',
    role: 'Challenge Organizers',
    bio: 'Organized the BirdCLEF 2026 competition with real-world test data.'
  }
]

export default function About() {
  return (
    <div className="min-h-screen bg-navy-900 text-white">
      {/* Header */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <h1 className="text-5xl font-bold mb-6">About BirdCLEF</h1>
          <p className="text-xl text-navy-300">
            A state-of-the-art bird species classification system developed for the BirdCLEF 2026 challenge.
          </p>
        </motion.div>
      </section>

      {/* Project Goal */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 border-b border-navy-700">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl font-bold mb-6">Project Goal</h2>
          <p className="text-lg text-navy-300 leading-relaxed">
            Develop an accurate, efficient AI model to classify bird species from 60-second audio recordings. This system
            can be used by ornithologists, citizen scientists, and bird watchers to identify species in real-world field
            conditions. The challenge motivates development of robust audio classification techniques that generalize across
            diverse recording environments and bird vocalizations.
          </p>
        </motion.div>
      </section>

      {/* BirdCLEF Dataset */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 border-b border-navy-700">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl font-bold mb-6">The BirdCLEF Dataset</h2>
          <div className="space-y-4 text-navy-300">
            <p>
              BirdCLEF is part of LifeCLEF, a large-scale species classification challenge. The dataset includes:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>234 bird species</strong> from diverse geographic regions</li>
              <li><strong>10,000+ hours</strong> of annotated audio recordings</li>
              <li><strong>Real-world conditions:</strong> background noise, multiple species, variable quality</li>
              <li><strong>Metadata:</strong> recording location, time of day, species identity</li>
            </ul>
            <p className="mt-4">
              Training data comes from Xeno-canto and Cornell Lab of Ornithology archives. The test set includes unseen
              species and challenging audio conditions to evaluate model generalization.
            </p>
          </div>
        </motion.div>
      </section>

      {/* Model Architecture */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 border-b border-navy-700">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl font-bold mb-6">Model Architecture</h2>

          <div className="space-y-6">
            <div className="bg-navy-800 border border-navy-600 rounded-lg p-6">
              <h3 className="font-semibold text-lg mb-3">Audio Preprocessing</h3>
              <p className="text-navy-300">
                Normalize all audio to 32 kHz mono. Split 60-second recordings into 12 consecutive 5-second windows to
                capture temporal patterns and enable class-specific time-of-day priors.
              </p>
            </div>

            <div className="bg-navy-800 border border-navy-600 rounded-lg p-6">
              <h3 className="font-semibold text-lg mb-3">Perch Embeddings + ProtoSSM</h3>
              <p className="text-navy-300 mb-2">
                <strong>Perch v2:</strong> ONNX model produces 1536-dimensional embeddings mapped to 234 species logits via
                per-species linear layers (perch_mapping).
              </p>
              <p className="text-navy-300">
                <strong>ProtoSSM:</strong> Sequence model incorporating site_id and hour_id contextual priors. Outputs
                smoothed class probabilities per window.
              </p>
            </div>

            <div className="bg-navy-800 border border-navy-600 rounded-lg p-6">
              <h3 className="font-semibold text-lg mb-3">Multi-Branch Refinement</h3>
              <p className="text-navy-300 mb-2">
                <strong>MLP Probes:</strong> Per-species MLPs refine predictions from Perch embeddings.
              </p>
              <p className="text-navy-300 mb-2">
                <strong>Residual Correction:</strong> ResidualSSM learns to correct misclassified windows by modeling
                time-series residuals.
              </p>
              <p className="text-navy-300">
                <strong>Temperature Scaling & Post-processing:</strong> Apply learned per-class temperature coefficients,
                sigmoid normalization, class-specific thresholds, and rank-aware smoothing.
              </p>
            </div>

            <div className="bg-navy-800 border border-navy-600 rounded-lg p-6">
              <h3 className="font-semibold text-lg mb-3">SED Ensemble</h3>
              <p className="text-navy-300">
                <strong>Sound Event Detection:</strong> 5-fold ONNX ensemble of SED models detects species presence in
                mel spectrograms. Outputs class probabilities per window.
              </p>
            </div>

            <div className="bg-navy-800 border border-navy-600 rounded-lg p-6">
              <h3 className="font-semibold text-lg mb-3">Rank-Aware Blending</h3>
              <p className="text-navy-300">
                Final predictions blend ProtoSSM and SED scores (0.6 Proto + 0.4 SED) using rank-aware blending to combine
                complementary model strengths. Apply aggregation across windows to produce per-species final scores.
              </p>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Tech Stack */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 border-b border-navy-700">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl font-bold mb-6">Technology Stack</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-lg mb-3">Backend</h3>
              <ul className="text-navy-300 space-y-1">
                <li>• FastAPI (REST API)</li>
                <li>• SQLAlchemy (ORM)</li>
                <li>• ONNX Runtime (inference)</li>
                <li>• Librosa (audio processing)</li>
                <li>• NumPy, SciPy (computation)</li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold text-lg mb-3">Frontend</h3>
              <ul className="text-navy-300 space-y-1">
                <li>• React + Vite (UI framework)</li>
                <li>• React Router (routing)</li>
                <li>• Tailwind CSS (styling)</li>
                <li>• Framer Motion (animations)</li>
                <li>• Recharts (visualizations)</li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold text-lg mb-3">Interactive Components</h3>
              <ul className="text-navy-300 space-y-1">
                <li>• React Flow (pipeline diagram)</li>
                <li>• WaveSurfer.js (audio playback)</li>
                <li>• React Joyride (guided tour)</li>
                <li>• Leaflet (map visualization)</li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold text-lg mb-3">Infrastructure</h3>
              <ul className="text-navy-300 space-y-1">
                <li>• MySQL (data storage)</li>
                <li>• Docker (containerization)</li>
                <li>• JWT (authentication)</li>
                <li>• CORS (cross-origin requests)</li>
              </ul>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Team Section */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl font-bold mb-6">Credits & Partners</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {teamConfig.map((member, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.2 }}
                viewport={{ once: true }}
                className="bg-navy-800 border border-navy-600 rounded-lg p-6"
              >
                <h3 className="text-lg font-semibold mb-1">{member.name}</h3>
                <p className="text-blue-400 text-sm mb-3">{member.role}</p>
                <p className="text-navy-300">{member.bio}</p>
              </motion.div>
            ))}
          </div>

          <div className="mt-12 text-center">
            <h3 className="text-lg font-semibold mb-3">Learn More</h3>
            <ul className="space-y-2 text-navy-300">
              <li>
                <a
                  href="https://www.imageclef.org/BirdCLEF2026"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 transition"
                >
                  BirdCLEF 2026 Challenge →
                </a>
              </li>
              <li>
                <a
                  href="https://www.xeno-canto.org/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 transition"
                >
                  Xeno-canto Bird Sound Archive →
                </a>
              </li>
              <li>
                <a
                  href="https://www.allaboutbirds.org/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 transition"
                >
                  Cornell Lab of Ornithology →
                </a>
              </li>
            </ul>
          </div>
        </motion.div>
      </section>
    </div>
  )
}
