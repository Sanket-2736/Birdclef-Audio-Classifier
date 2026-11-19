
import { motion } from 'framer-motion'

/* ───────── Neo-brutalist theme (matching HowItWorks) ───────── */

const C = {
  y: '#FDB900',
  b: '#3B6CF6',
  r: '#F2415A',
  g: '#10B981',
  p: '#E5197F',
  k: '#0a0a0a',
  bg: '#FFF9E8',
  white: '#FFFFFF',
  muted: '#555555'
}

const BOX = 'border-[3px] border-black shadow-[6px_6px_0_#000]'
const BTN =
  'border-[3px] border-black font-bold shadow-[4px_4px_0_#000] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none transition-all'

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

.about-page {
  font-family: 'Space Grotesk', system-ui, sans-serif;
}

.about-page .mono {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}

@keyframes about-float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-7px); }
}

@keyframes about-marquee {
  from { transform: translateX(0); }
  to { transform: translateX(-50%); }
}

.about-page .float {
  animation: about-float 4s ease-in-out infinite;
}

.about-page .marquee {
  animation: about-marquee 25s linear infinite;
}

@media (prefers-reduced-motion: reduce) {
  .about-page *,
  .about-page *::before,
  .about-page *::after {
    animation: none !important;
    transition: none !important;
  }
}
`

const teamConfig = [
  {
    name: 'BirdCLEF Team',
    role: 'Project Lead',
    bio: 'Competition-winning bird species classification system.',
    color: C.y,
    number: '01'
  },
  {
    name: 'Cornell Lab of Ornithology',
    role: 'Data & Expertise',
    bio: 'Curated bird call dataset and domain guidance for model development.',
    color: C.b,
    number: '02'
  },
  {
    name: 'LifeCLEF & Kaggle',
    role: 'Challenge Organizers',
    bio: 'Organized the BirdCLEF 2026 competition with real-world test data.',
    color: C.p,
    number: '03'
  }
]

const architecture = [
  {
    number: '01',
    title: 'Audio Preprocessing',
    tag: 'INPUT PIPELINE',
    color: C.y,
    description: [
      'Normalize all audio to 32 kHz mono. Split 60-second recordings into 12 consecutive 5-second windows to capture temporal patterns and enable class-specific time-of-day priors.'
    ]
  },
  {
    number: '02',
    title: 'Perch Embeddings + ProtoSSM',
    tag: 'FEATURE EXTRACTION',
    color: C.b,
    description: [
      'Perch v2: ONNX model produces 1536-dimensional embeddings mapped to 234 species logits via per-species linear layers (perch_mapping).',
      'ProtoSSM: Sequence model incorporating site_id and hour_id contextual priors. Outputs smoothed class probabilities per window.'
    ]
  },
  {
    number: '03',
    title: 'Multi-Branch Refinement',
    tag: 'PREDICTION REFINEMENT',
    color: C.p,
    description: [
      'MLP Probes: Per-species MLPs refine predictions from Perch embeddings.',
      'Residual Correction: ResidualSSM learns to correct misclassified windows by modeling time-series residuals.',
      'Temperature Scaling & Post-processing: Apply learned per-class temperature coefficients, sigmoid normalization, class-specific thresholds, and rank-aware smoothing.'
    ]
  },
  {
    number: '04',
    title: 'SED Ensemble',
    tag: 'SOUND DETECTION',
    color: C.g,
    description: [
      'Sound Event Detection: 5-fold ONNX ensemble of SED models detects species presence in mel spectrograms. Outputs class probabilities per window.'
    ]
  },
  {
    number: '05',
    title: 'Rank-Aware Blending',
    tag: 'FINAL PREDICTION',
    color: C.r,
    description: [
      'Final predictions blend ProtoSSM and SED scores (0.6 Proto + 0.4 SED) using rank-aware blending to combine complementary model strengths. Apply aggregation across windows to produce per-species final scores.'
    ]
  }
]

const technologies = [
  {
    title: 'Backend',
    color: C.y,
    icon: '⚙️',
    items: [
      'FastAPI (REST API)',
      'SQLAlchemy (ORM)',
      'ONNX Runtime (inference)',
      'Librosa (audio processing)',
      'NumPy, SciPy (computation)'
    ]
  },
  {
    title: 'Frontend',
    color: C.b,
    icon: '💻',
    items: [
      'React + Vite (UI framework)',
      'React Router (routing)',
      'Tailwind CSS (styling)',
      'Framer Motion (animations)',
      'Recharts (visualizations)'
    ]
  },
  {
    title: 'Interactive Components',
    color: C.p,
    icon: '✨',
    items: [
      'React Flow (pipeline diagram)',
      'WaveSurfer.js (audio playback)',
      'React Joyride (guided tour)',
      'Leaflet (map visualization)'
    ]
  },
  {
    title: 'Infrastructure',
    color: C.g,
    icon: '🛠️',
    items: [
      'MySQL (data storage)',
      'Docker (containerization)',
      'JWT (authentication)',
      'CORS (cross-origin requests)'
    ]
  }
]

const resources = [
  {
    name: 'BirdCLEF 2026 Challenge',
    description: 'Explore the competition',
    url: 'https://www.imageclef.org/BirdCLEF2026',
    color: C.y
  },
  {
    name: 'Xeno-canto Bird Sound Archive',
    description: 'Explore bird sound recordings',
    url: 'https://www.xeno-canto.org/',
    color: C.b
  },
  {
    name: 'Cornell Lab of Ornithology',
    description: 'Discover bird research and resources',
    url: 'https://www.allaboutbirds.org/',
    color: C.p
  }
]

/* ───────── Reusable components ───────── */

function SectionLabel({ children, color = C.y }) {
  return (
    <span
      className="mono inline-block px-3 py-1.5 text-xs font-bold uppercase tracking-wider border-2 border-black"
      style={{ background: color, color: '#000' }}
    >
      {children}
    </span>
  )
}

function SectionHeading({ eyebrow, title, subtitle, color = C.y }) {
  return (
    <div className="mb-10">
      <SectionLabel color={color}>{eyebrow}</SectionLabel>
      <h2 className="mt-5 text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-black">
        {title}
      </h2>
      {subtitle && (
        <p className="mt-4 text-base sm:text-lg text-neutral-600 max-w-2xl leading-relaxed">
          {subtitle}
        </p>
      )}
    </div>
  )
}

function InfoCard({ children, color = C.y, className = '' }) {
  return (
    <div
      className={`${BOX} bg-white ${className}`}
      style={{ borderColor: C.k }}
    >
      {children}
    </div>
  )
}

/* ───────── About Page ───────── */

export default function About() {
  return (
    <div
      className="about-page min-h-screen text-black overflow-hidden"
      style={{ background: C.bg }}
    >
      <style>{CSS}</style>

      {/* ───────── HERO ───────── */}

      <section className="relative px-4 sm:px-6 lg:px-8 pt-16 sm:pt-24 pb-20">
        <div className="max-w-7xl mx-auto">

          <motion.div
            initial={{ opacity: 0, y: 25 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
          >
            <div className="flex flex-wrap gap-3 items-center mb-8">
              <SectionLabel color={C.y}>
                PROJECT OVERVIEW
              </SectionLabel>

              <span className="mono text-xs font-bold text-neutral-500">
                BIRDCLEF 2026
              </span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[1.35fr_0.65fr] gap-12 items-center">

              <div>
                <h1 className="text-5xl sm:text-6xl lg:text-8xl font-bold leading-[0.98] tracking-tight">
                  ABOUT
                  <br />
                  <span
                    className="inline-block px-3 mt-2"
                    style={{
                      background: C.y,
                      border: '3px solid black',
                      boxShadow: '6px 6px 0 #000'
                    }}
                  >
                    BIRDCLEF.
                  </span>
                </h1>

                <p className="mt-9 text-lg sm:text-xl text-neutral-700 leading-relaxed max-w-2xl">
                  A state-of-the-art bird species classification system
                  developed for the BirdCLEF 2026 challenge.
                  Combining audio processing, machine learning, and
                  contextual information to identify bird species
                  from real-world recordings.
                </p>

                <div className="mt-9 flex flex-wrap gap-3">
                  <span
                    className="mono text-xs font-bold px-4 py-2 border-2 border-black"
                    style={{ background: C.b, color: 'white' }}
                  >
                    AI / ML
                  </span>
                  <span
                    className="mono text-xs font-bold px-4 py-2 border-2 border-black"
                    style={{ background: C.p, color: 'white' }}
                  >
                    AUDIO CLASSIFICATION
                  </span>
                  <span
                    className="mono text-xs font-bold px-4 py-2 border-2 border-black"
                    style={{ background: C.g, color: 'black' }}
                  >
                    BIRD SPECIES
                  </span>
                </div>
              </div>

              <motion.div
                initial={{ opacity: 0, rotate: 5, scale: 0.9 }}
                animate={{ opacity: 1, rotate: 0, scale: 1 }}
                transition={{ duration: 0.8, delay: 0.2 }}
                className="relative"
              >
                <div
                  className={`${BOX} p-7 sm:p-9`}
                  style={{ background: C.y }}
                >
                  <div className="mono text-xs font-bold mb-8">
                    SYSTEM / OVERVIEW
                  </div>

                  <div className="text-6xl sm:text-7xl mb-5 float">
                    🐦
                  </div>

                  <h3 className="text-2xl sm:text-3xl font-bold">
                    Listen.
                    <br />
                    Analyze.
                    <br />
                    Identify.
                  </h3>

                  <div className="mt-8 pt-5 border-t-[3px] border-black flex justify-between items-center">
                    <span className="mono text-xs font-bold">
                      BIRDCLEF 2026
                    </span>
                    <span className="mono text-xs font-bold">
                      AI SYSTEM
                    </span>
                  </div>
                </div>

                <div
                  className="absolute -bottom-5 -right-3 sm:-right-5 px-4 py-3 border-[3px] border-black font-bold shadow-[4px_4px_0_#000] rotate-3"
                  style={{ background: C.p, color: 'white' }}
                >
                  SOUND → SPECIES
                </div>
              </motion.div>

            </div>
          </motion.div>
        </div>
      </section>

      {/* ───────── MARQUEE ───────── */}

      <div
        className="overflow-hidden border-y-[3px] border-black py-4"
        style={{ background: C.k, color: 'white' }}
      >
        <div className="marquee flex w-max gap-10 whitespace-nowrap mono text-sm font-bold">
          {Array.from({ length: 2 }).map((_, i) => (
            <span key={i} className="flex gap-10">
              <span>◈ BIRD SPECIES CLASSIFICATION</span>
              <span style={{ color: C.y }}>◈ AUDIO INTELLIGENCE</span>
              <span>◈ MACHINE LEARNING</span>
              <span style={{ color: C.p }}>◈ BIRDCLEF 2026</span>
              <span>◈ SOUND EVENT DETECTION</span>
            </span>
          ))}
        </div>
      </div>

      {/* ───────── PROJECT GOAL ───────── */}

      <section className="px-4 sm:px-6 lg:px-8 py-20">
        <div className="max-w-7xl mx-auto">

          <SectionHeading
            eyebrow="01 / THE MISSION"
            title="What are we building?"
            subtitle="Understanding the purpose behind the BirdCLEF classification system."
            color={C.b}
          />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-7">

            <div className="lg:col-span-2">
              <InfoCard className="p-7 sm:p-9 h-full">
                <div className="mono text-xs font-bold text-neutral-400 mb-5">
                  PROJECT GOAL
                </div>

                <h3 className="text-2xl sm:text-3xl font-bold mb-5">
                  Turning bird sounds into meaningful predictions.
                </h3>

                <p className="text-neutral-600 text-base sm:text-lg leading-relaxed">
                  Develop an accurate, efficient AI model to classify bird
                  species from 60-second audio recordings. This system
                  can be used by ornithologists, citizen scientists, and
                  bird watchers to identify species in real-world field
                  conditions. The challenge motivates development of
                  robust audio classification techniques that generalize
                  across diverse recording environments and bird
                  vocalizations.
                </p>

                <div className="mt-8 flex flex-wrap gap-2">
                  {['Audio Processing', 'Deep Learning', 'Classification', 'Contextual Priors'].map((item) => (
                    <span
                      key={item}
                      className="mono text-[10px] sm:text-xs font-bold px-3 py-2 border-2 border-black"
                      style={{ background: C.y }}
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </InfoCard>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-6">

              <InfoCard className="p-6" color={C.y}>
                <div className="mono text-xs font-bold text-neutral-500">
                  SPECIES
                </div>
                <div className="text-5xl font-bold mt-3">234</div>
                <p className="text-sm text-neutral-600 mt-2">
                  Bird species included in the dataset
                </p>
              </InfoCard>

              <InfoCard className="p-6" color={C.p}>
                <div className="mono text-xs font-bold text-neutral-500">
                  RECORDINGS
                </div>
                <div className="text-4xl sm:text-5xl font-bold mt-3">
                  10,000+
                </div>
                <p className="text-sm text-neutral-600 mt-2">
                  Hours of annotated audio recordings
                </p>
              </InfoCard>

            </div>
          </div>
        </div>
      </section>

      {/* ───────── DATASET ───────── */}

      <section
        className="px-4 sm:px-6 lg:px-8 py-20 border-y-[3px] border-black"
        style={{ background: '#FFF0C2' }}
      >
        <div className="max-w-7xl mx-auto">

          <SectionHeading
            eyebrow="02 / DATA"
            title="The BirdCLEF Dataset"
            subtitle="A large-scale species classification challenge with diverse recordings and real-world conditions."
            color={C.p}
          />

          <InfoCard className="p-7 sm:p-9">

            <p className="text-neutral-600 text-lg mb-7">
              BirdCLEF is part of LifeCLEF, a large-scale species
              classification challenge. The dataset includes:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">

              {[
                {
                  title: '234 bird species',
                  description: 'From diverse geographic regions',
                  color: C.y,
                  icon: '🐦'
                },
                {
                  title: '10,000+ hours',
                  description: 'Of annotated audio recordings',
                  color: C.b,
                  icon: '🎧'
                },
                {
                  title: 'Real-world conditions',
                  description: 'Background noise, multiple species, variable quality',
                  color: C.p,
                  icon: '🌿'
                },
                {
                  title: 'Rich metadata',
                  description: 'Recording location, time of day, species identity',
                  color: C.g,
                  icon: '📍'
                }
              ].map((item, index) => (
                <motion.div
                  key={item.title}
                  initial={{ opacity: 0, y: 15 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  className="border-[3px] border-black p-5 sm:p-6"
                  style={{ background: item.color }}
                >
                  <div className="text-3xl mb-4">{item.icon}</div>
                  <h3 className="text-xl font-bold">{item.title}</h3>
                  <p className="mt-2 text-sm text-black/70">
                    {item.description}
                  </p>
                </motion.div>
              ))}

            </div>

            <div className="mt-8 border-t-[3px] border-black pt-7">
              <div className="mono text-xs font-bold mb-3">
                DATA SOURCES
              </div>

              <p className="text-neutral-600 leading-relaxed">
                Training data comes from Xeno-canto and Cornell Lab
                of Ornithology archives. The test set includes unseen
                species and challenging audio conditions to evaluate
                model generalization.
              </p>
            </div>

          </InfoCard>
        </div>
      </section>

      {/* ───────── MODEL ARCHITECTURE ───────── */}

      <section className="px-4 sm:px-6 lg:px-8 py-20">
        <div className="max-w-7xl mx-auto">

          <SectionHeading
            eyebrow="03 / THE ENGINE"
            title="Model Architecture"
            subtitle="A multi-stage audio classification pipeline that combines feature extraction, sequence modeling, refinement, and ensemble predictions."
            color={C.y}
          />

          <div className="relative">

            <div className="absolute left-[22px] sm:left-[29px] top-8 bottom-8 w-[3px] bg-black hidden sm:block" />

            <div className="space-y-7">
              {architecture.map((item, index) => (
                <motion.div
                  key={item.number}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.08 }}
                  className="relative sm:pl-20"
                >

                  <div
                    className="hidden sm:flex absolute left-0 top-6 z-10 w-[60px] h-[60px] border-[3px] border-black items-center justify-center font-bold text-xl shadow-[3px_3px_0_#000]"
                    style={{ background: item.color }}
                  >
                    {item.number}
                  </div>

                  <InfoCard className="overflow-hidden">
                    <div
                      className="px-5 sm:px-7 py-4 border-b-[3px] border-black flex flex-wrap gap-3 items-center justify-between"
                      style={{ background: item.color }}
                    >
                      <div className="flex items-center gap-3">
                        <span className="mono font-bold text-sm sm:hidden">
                          {item.number}
                        </span>
                        <h3 className="text-lg sm:text-xl font-bold">
                          {item.title}
                        </h3>
                      </div>

                      <span className="mono text-[10px] font-bold border-2 border-black px-2 py-1 bg-white">
                        {item.tag}
                      </span>
                    </div>

                    <div className="p-5 sm:p-7 space-y-4">
                      {item.description.map((paragraph, i) => (
                        <p
                          key={i}
                          className="text-neutral-600 leading-relaxed"
                        >
                          {paragraph}
                        </p>
                      ))}
                    </div>
                  </InfoCard>

                </motion.div>
              ))}
            </div>

          </div>

          <div
            className="mt-10 p-6 sm:p-8 border-[3px] border-black shadow-[6px_6px_0_#000]"
            style={{ background: C.k, color: 'white' }}
          >
            <div className="mono text-xs font-bold mb-3" style={{ color: C.y }}>
              FINAL ENSEMBLE WEIGHTING
            </div>

            <div className="flex flex-col sm:flex-row gap-6 items-center">
              <div className="flex-1 w-full">
                <div className="flex justify-between mono text-xs font-bold mb-2">
                  <span>PROTO SSM</span>
                  <span>60%</span>
                </div>
                <div className="h-5 border-2 border-white">
                  <div className="h-full" style={{ width: '60%', background: C.y }} />
                </div>
              </div>

              <div className="flex-1 w-full">
                <div className="flex justify-between mono text-xs font-bold mb-2">
                  <span>SED</span>
                  <span>40%</span>
                </div>
                <div className="h-5 border-2 border-white">
                  <div className="h-full" style={{ width: '40%', background: C.p }} />
                </div>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* ───────── TECHNOLOGY STACK ───────── */}

      <section
        className="px-4 sm:px-6 lg:px-8 py-20 border-y-[3px] border-black"
        style={{ background: '#E9EDFF' }}
      >
        <div className="max-w-7xl mx-auto">

          <SectionHeading
            eyebrow="04 / TECHNOLOGY"
            title="Built With The Right Tools."
            subtitle="The technologies powering the backend, frontend, interactive experience, and infrastructure."
            color={C.b}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-7">

            {technologies.map((tech, index) => (
              <motion.div
                key={tech.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <InfoCard className="h-full overflow-hidden">

                  <div
                    className="p-5 sm:p-6 border-b-[3px] border-black flex items-center gap-4"
                    style={{ background: tech.color }}
                  >
                    <div className="text-3xl">{tech.icon}</div>
                    <div>
                      <div className="mono text-[10px] font-bold opacity-60">
                        TECHNOLOGY MODULE / 0{index + 1}
                      </div>
                      <h3 className="text-xl font-bold mt-1">
                        {tech.title}
                      </h3>
                    </div>
                  </div>

                  <div className="p-6 space-y-3">
                    {tech.items.map((item) => (
                      <div
                        key={item}
                        className="flex items-start gap-3 text-neutral-700"
                      >
                        <span className="font-bold text-black">→</span>
                        <span className="text-sm sm:text-base">
                          {item}
                        </span>
                      </div>
                    ))}
                  </div>

                </InfoCard>
              </motion.div>
            ))}

          </div>
        </div>
      </section>

      {/* ───────── TEAM & PARTNERS ───────── */}

      <section className="px-4 sm:px-6 lg:px-8 py-20">
        <div className="max-w-7xl mx-auto">

          <SectionHeading
            eyebrow="05 / ACKNOWLEDGEMENTS"
            title="Credits & Partners"
            subtitle="The organizations and contributors associated with the BirdCLEF project."
            color={C.p}
          />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-7">

            {teamConfig.map((member, index) => (
              <motion.div
                key={member.number}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.15 }}
              >
                <InfoCard className="h-full overflow-hidden">

                  <div
                    className="p-6 border-b-[3px] border-black"
                    style={{ background: member.color }}
                  >
                    <div className="mono text-xs font-bold">
                      CONTRIBUTOR / {member.number}
                    </div>
                    <div className="text-4xl mt-5">
                      {index === 0 ? '🧑‍💻' : index === 1 ? '🦉' : '🏆'}
                    </div>
                  </div>

                  <div className="p-6">
                    <h3 className="text-xl font-bold">
                      {member.name}
                    </h3>

                    <p className="mono text-xs font-bold mt-3 text-neutral-500">
                      {member.role.toUpperCase()}
                    </p>

                    <p className="text-neutral-600 mt-4 leading-relaxed text-sm">
                      {member.bio}
                    </p>
                  </div>

                </InfoCard>
              </motion.div>
            ))}

          </div>
        </div>
      </section>

      {/* ───────── LEARN MORE ───────── */}

      <section
        className="px-4 sm:px-6 lg:px-8 py-20 border-t-[3px] border-black"
        style={{ background: C.y }}
      >
        <div className="max-w-7xl mx-auto">

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_1fr] gap-12 items-center">

            <div>
              <SectionLabel color={C.white}>
                EXPLORE FURTHER
              </SectionLabel>

              <h2 className="mt-6 text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight">
                Want to
                <br />
                Learn More?
              </h2>

              <p className="mt-5 text-neutral-700 text-lg max-w-lg leading-relaxed">
                Explore the challenge, discover bird sound recordings,
                and learn more about ornithology through these resources.
              </p>
            </div>

            <div className="space-y-5">
              {resources.map((resource, index) => (
                <motion.a
                  key={resource.name}
                  href={resource.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  initial={{ opacity: 0, x: 20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.12 }}
                  className="group flex items-center justify-between gap-4 p-5 bg-white border-[3px] border-black shadow-[5px_5px_0_#000] hover:translate-x-1 hover:-translate-y-1 hover:shadow-[7px_7px_0_#000] transition-all"
                >
                  <div className="flex items-center gap-4">
                    <div
                      className="w-11 h-11 shrink-0 border-2 border-black flex items-center justify-center font-bold"
                      style={{ background: resource.color }}
                    >
                      0{index + 1}
                    </div>

                    <div>
                      <h3 className="font-bold text-sm sm:text-base">
                        {resource.name}
                      </h3>
                      <p className="text-xs text-neutral-500 mt-1">
                        {resource.description}
                      </p>
                    </div>
                  </div>

                  <span className="text-xl font-bold group-hover:translate-x-1 transition-transform">
                    ↗
                  </span>
                </motion.a>
              ))}
            </div>

          </div>
        </div>
      </section>

      {/* ───────── FOOTER STRIP ───────── */}

      <footer
        className="px-4 sm:px-6 lg:px-8 py-6 border-t-[3px] border-black"
        style={{ background: C.k, color: 'white' }}
      >
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-3">
          <span className="mono text-xs font-bold">
            BIRDCLEF 2026
          </span>

          <span className="mono text-[10px] text-neutral-400">
            LISTEN • ANALYZE • IDENTIFY
          </span>

          <span className="mono text-xs font-bold" style={{ color: C.y }}>
            ABOUT THE PROJECT
          </span>
        </div>
      </footer>

    </div>
  )
}
