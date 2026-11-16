import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import Joyride from 'react-joyride'
import demoData from '../data/demoResult.json'

/* ───────── theme (neo-brutalist: thick black borders, hard shadows, flat colour) ───────── */
const C = { y: '#FDB900', b: '#3B6CF6', r: '#F2415A', g: '#10B981', p: '#E5197F', k: '#0a0a0a' }
const BOX = 'border-[3px] border-black shadow-[6px_6px_0_#000]'
const BTN = 'border-[3px] border-black font-bold shadow-[4px_4px_0_#000] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none transition-all'
const CSS = `@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=JetBrains+Mono:wght@400;700&display=swap');
.hiw{font-family:'Space Grotesk',system-ui,sans-serif}.hiw .mono{font-family:'JetBrains Mono',ui-monospace,monospace}
@keyframes hiw-noise{0%{background-position:0 0}25%{background-position:-40px 22px}50%{background-position:30px -35px}75%{background-position:-22px -12px}100%{background-position:12px 30px}}
@keyframes hiw-flick{0%,100%{opacity:1}50%{opacity:.965}}
@media (prefers-reduced-motion:reduce){.hiw *{animation:none!important}}`
const NOISE = `url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/></filter><rect width='160' height='160' filter='url(%23n)'/></svg>")`

/* ───────── data: real clip if src/data/tvAudio.json exists, else demo fallback ───────── */
const rng = (s) => () => (s = (s * 16807) % 2147483647) / 2147483647
const real = Object.values(import.meta.glob('../data/tvAudio.json', { eager: true, import: 'default' }))[0]
const DUR = real?.duration ?? demoData.real_duration_sec ?? 28
const NW = Math.min(12, Math.ceil(DUR / 5))
const PEAKS = real?.peaks ?? Array.from({ length: 120 }, (_, i) => demoData.waveform_peaks[Math.floor((i * demoData.waveform_peaks.length) / 120)] ?? 0.2)
const MEL = real?.mel ?? (() => { const r = rng(7); return Array.from({ length: 32 }, (_, b) => Array.from({ length: 120 }, (_, f) => Math.min(255, Math.round(210 * Math.exp(-b / 14) * (0.5 + 0.5 * r()) + (Math.sin(f / 9 + b / 3) > 0.7 ? 50 : 0))))) })()
const BS = demoData.branch_scores
const SP = BS.species
const wf = (w) => [(w * 5) / DUR, Math.min(1, ((w + 1) * 5) / DUR)]
const STOPS = [[0, 0, 4], [59, 15, 112], [140, 41, 129], [222, 73, 104], [254, 159, 109], [252, 253, 191]]
const cm = (v) => { const t = (Math.max(0, Math.min(255, v)) / 255) * 5, i = Math.min(4, Math.floor(t)), f = t - i; const a = STOPS[i], b = STOPS[i + 1]; return `rgb(${a.map((x, k) => Math.round(x + (b[k] - x) * f)).join(',')})` }
const avg = (b, s) => BS[b].reduce((a, r) => a + r[s], 0) / BS[b].length
const col = (b, s) => BS[b].map((r) => r[s])
const prob = (p, T) => { const q = Math.min(0.999, Math.max(0.001, p)); return 1 / (1 + Math.exp(-Math.log(q / (1 - q)) / T)) }
const rank = (arr) => { const o = arr.map((v, i) => [v, i]).sort((a, b) => a[0] - b[0]), r = []; o.forEach(([, i], k) => (r[i] = k / (arr.length - 1))); return r }
const blend = (w) => { const p = SP.map((_, s) => avg('proto', s)), e = SP.map((_, s) => avg('sed', s)), rp = rank(p), re = rank(e); return SP.map((s, i) => ({ ...s, p: p[i], e: e[i], score: w * rp[i] + (1 - w) * re[i] })).sort((a, b) => b.score - a.score) }
const EVAL_METRICS = { mAP: null, 'F1-score': null, Precision: null, Recall: null, AUC: null } // ← put your validation numbers (0-1) here

/* ───────── small building blocks ───────── */
const Chip = ({ children, color = '#000', text = '#fff', className = '' }) => (
  <span className={`mono inline-block px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${className}`} style={{ background: color, color: text }}>{children}</span>
)
const Pill = ({ on, color, children, ...p }) => (
  <button {...p} className={`mono px-2.5 py-1 text-[11px] font-bold border-2 border-black transition-all ${on ? 'translate-x-[2px] translate-y-[2px]' : 'shadow-[3px_3px_0_#000]'}`} style={{ background: on ? color : '#fff', color: '#000' }}>{children}</button>
)
const Bars = ({ vals, color = C.y, h = 70, lit }) => (
  <div className="flex items-end gap-[3px] w-full" style={{ height: h }}>
    {vals.map((v, i) => (
      <motion.div key={i} initial={{ height: 0 }} animate={{ height: `${Math.max(2, v * 100)}%` }} transition={{ delay: i * 0.03, type: 'spring', stiffness: 160, damping: 18 }}
        className="flex-1 border-2 border-black" style={{ background: lit?.(i) ? color : '#e5e5e5', opacity: i >= NW && lit ? 0.35 : 1 }} title={v.toFixed(2)} />
    ))}
  </div>
)
function Spec({ m = MEL, from = 0, to = 1, className = '', children }) {
  const cols = useMemo(() => {
    const n = m[0].length, a = Math.floor(from * n), z = Math.max(a + 1, Math.ceil(to * n))
    return Array.from({ length: z - a }, (_, i) => `linear-gradient(to top,${m.map((row, b) => `${cm(row[a + i] ?? 0)} ${((b / m.length) * 100).toFixed(1)}% ${(((b + 1) / m.length) * 100).toFixed(1)}%`).join(',')})`)
  }, [m, from, to])
  return <div className={`relative flex overflow-hidden bg-black ${className}`}>{cols.map((g, i) => <div key={i} className="flex-1" style={{ background: g }} />)}{children}</div>
}
const Wave = ({ h = 70, color = C.b, fill = 1, dim }) => (
  <div className="flex items-center gap-[1px]" style={{ height: h, width: `${fill * 100}%` }}>
    {PEAKS.map((p, i) => <motion.div key={i} initial={{ scaleY: 0 }} animate={{ scaleY: 1 }} transition={{ delay: i * 0.004 }} className="flex-1" style={{ height: `${Math.max(4, p * 100)}%`, background: dim ? '#6b7280' : color }} />)}
  </div>
)
const Arrow = ({ c = '#fff' }) => <motion.span animate={{ x: [0, 5, 0] }} transition={{ repeat: Infinity, duration: 1.2 }} className="mono font-bold text-xl shrink-0" style={{ color: c }}>▶</motion.span>
const Node = ({ children, color = '#fff', on, onClick, className = '' }) => (
  <button onClick={onClick} className={`border-[3px] border-black px-2 py-1.5 text-[11px] font-bold text-black text-center leading-tight ${on ? 'translate-x-[2px] translate-y-[2px]' : 'shadow-[3px_3px_0_#fff]'} ${className}`} style={{ background: color }}>{children}</button>
)
const SpeciesPick = ({ s, setS }) => (
  <div className="flex flex-wrap gap-1.5">{SP.map((x, i) => <Pill key={x.code} on={s === i} color={C.y} onClick={() => setS(i)}>{x.common_name}</Pill>)}</div>
)
const Tabs = ({ items, v, set, color }) => <div className="flex flex-wrap gap-1.5">{items.map((t, i) => <Pill key={t} on={v === i} color={color} onClick={() => set(i)}>{t}</Pill>)}</div>
const Cap = ({ children }) => <p className="mono text-[11px] text-white/70 leading-snug">{children}</p>
const WinPick = ({ w, setW }) => <div className="flex flex-wrap gap-1">{Array.from({ length: NW }, (_, i) => <Pill key={i} on={w === i} color={C.g} onClick={() => setW(i)}>{i + 1}</Pill>)}</div>

/* ───────── TV channels (each screen is plain CSS + framer-motion) ───────── */
function S1() {
  const r = rng(3)
  const tail = Array.from({ length: 40 }, (_, i) => Math.max(0.03, Math.exp(-i / 9) * (0.8 + 0.2 * r())))
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-2">{[['Pantanal', 'BirdCLEF 2026 subset', C.y], ['.ogg · ~32 kHz', 'weak labels', C.b], ['234 species', 'multi-label', C.g]].map(([a, b, c]) => <div key={a} className="border-[3px] border-black p-2 text-black" style={{ background: c }}><b className="block text-sm">{a}</b><span className="mono text-[10px]">{b}</span></div>)}</div>
      <Cap>Class imbalance: a few species have many recordings, most have few (shape is illustrative)</Cap>
      <Bars vals={tail} color={C.r} h={90} lit={() => true} />
      <Cap>Demo clip · {DUR.toFixed(1)} s</Cap>
      <audio controls src="/demo.ogg" className="w-full h-9" />
    </div>
  )
}
function S2() {
  const [st, setSt] = useState(0)
  const fill = st >= 2 ? Math.min(1, DUR / 60) : 1
  return (
    <div className="space-y-3">
      <Tabs items={['1 Raw', '2 32 kHz mono', '3 Pad to 60 s', '4 Split ×12']} v={st} set={setSt} color={C.y} />
      <div className="relative border-[3px] border-black bg-white p-2" style={{ background: st >= 2 ? 'repeating-linear-gradient(45deg,#ddd 0 6px,#fff 6px 12px)' : '#fff' }}>
        <Wave h={90} fill={fill} color={st === 0 ? C.r : C.b} />
        {st === 3 && <div className="absolute inset-2 flex">{Array.from({ length: 12 }, (_, i) => <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }} className="flex-1 border-l-2 border-black text-[9px] mono text-black font-bold pl-0.5" style={{ background: i < NW ? `${[C.y, C.g, C.b, C.r][i % 4]}55` : 'transparent' }}>{i + 1}</motion.div>)}</div>}
      </div>
      <Cap>{['The original recording, whatever its format and sample rate.', 'Resampled to 32 kHz and mixed down to mono so every clip looks the same.', `This clip is ${DUR.toFixed(1)} s, so the grey hatched part is silence added up to 60 s (longer clips are cut).`, `60 s ÷ 5 s = 12 windows. Only the first ${NW} hold real audio.`][st]}</Cap>
    </div>
  )
}
function S3() {
  const r = useMemo(() => rng(11), [])
  const emb = useMemo(() => Array.from({ length: 12 * 48 }, () => 255 * r() ** 2), [r])
  return (
    <div className="space-y-2">
      <Cap>12 windows → Perch → one 1536-number fingerprint per window (embedding values are illustrative)</Cap>
      <div className="flex gap-1">{Array.from({ length: 12 }, (_, i) => <Spec key={i} from={wf(i)[0]} to={wf(i)[1]} className={`flex-1 h-14 border-2 border-black ${i >= NW ? 'opacity-25' : ''}`} />)}</div>
      <div className="flex items-center gap-2"><Node color={C.y}>Perch<br />model</Node><Arrow /><div className="grid flex-1 gap-[1px]" style={{ gridTemplateColumns: 'repeat(48,1fr)' }}>{emb.map((v, i) => <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: (i % 48) * 0.01 }} className="h-[7px]" style={{ background: cm(v) }} />)}</div></div>
      <Cap>12 rows × 1536 columns (shown downsampled). Perch also gives class scores, mapped onto your 234 species.</Cap>
    </div>
  )
}
function S4() {
  const [w, setW] = useState(0)
  const [a, z] = wf(w), n = MEL[0].length, i0 = Math.floor(a * n), i1 = Math.max(i0 + 1, Math.ceil(z * n))
  const vals = MEL.flatMap((row) => row.slice(i0, i1)).map((v) => v / 255), mean = vals.reduce((s, v) => s + v, 0) / vals.length
  const stats = [['mean', mean], ['max', Math.max(...vals)], ['std', Math.sqrt(vals.reduce((s, v) => s + (v - mean) ** 2, 0) / vals.length)]]
  return (
    <div className="space-y-2">
      <WinPick w={w} setW={setW} />
      <div className="flex gap-1.5">{[w - 1, w, w + 1].map((k, j) => <div key={j} className="flex-1"><Cap>{['previous', 'current', 'next'][j]}</Cap>{k >= 0 && k < 12 ? <Spec from={wf(k)[0]} to={wf(k)[1]} className={`h-14 border-2 ${j === 1 ? 'border-[#FDB900]' : 'border-black opacity-60'}`} /> : <div className="h-14 border-2 border-dashed border-white/40" />}</div>)}</div>
      <div className="flex gap-3 items-end"><div className="flex-1"><Bars vals={stats.map((s) => s[1])} color={C.b} h={60} lit={() => true} /><div className="flex justify-around mono text-[10px] text-white/70">{stats.map((s) => <span key={s[0]}>{s[0]} {s[1].toFixed(2)}</span>)}</div></div>
        <div className="flex-1 space-y-1"><Cap>PCA squeezes 1536 numbers into 64</Cap><div className="h-3 border-2 border-black bg-white" /><motion.div key={w} initial={{ width: '100%' }} animate={{ width: '4.2%' }} transition={{ duration: 1 }} className="h-3 border-2 border-black" style={{ background: C.y }} /></div></div>
    </div>
  )
}
function S5() {
  const [t, setT] = useState(0), [w, setW] = useState(0)
  const [a, z] = wf(w), [a2, z2] = wf((w + 3) % NW)
  const m = useMemo(() => { const r = rng(5), n = MEL[0].length, s = Math.floor(a * n), s2 = Math.floor(a2 * n); const len = Math.max(1, Math.ceil(z * n) - s)
    return MEL.map((row) => Array.from({ length: len }, (_, f) => t === 1 ? 0.6 * (row[s + f] ?? 0) + 0.4 * (row[s2 + f] ?? 0) : t === 2 ? Math.min(255, (row[s + f] ?? 0) * 0.7 + r() * 90) : row[s + f] ?? 0)) }, [t, a, z, a2])
  return (
    <div className="space-y-2">
      <Chip color={C.r}>training only</Chip>
      <Tabs items={['Original', 'Mixup', 'Noise', 'SpecAugment']} v={t} set={setT} color={C.r} />
      <WinPick w={w} setW={setW} />
      <Spec m={m} className="h-36 border-[3px] border-black">
        {t === 3 && <><div className="absolute inset-y-0 bg-black/90" style={{ left: '30%', width: '14%' }} /><div className="absolute inset-y-0 bg-black/90" style={{ left: '68%', width: '9%' }} /><div className="absolute inset-x-0 bg-black/90" style={{ top: '22%', height: '16%' }} /></>}
      </Spec>
      <Cap>{['The clean 5 s window.', 'Two windows blended 60/40 so the model learns to handle overlapping sounds.', 'Random noise added so it copes with wind and insects.', 'Black bars hide random time and frequency ranges so it cannot rely on one cue.'][t]}</Cap>
    </div>
  )
}
function S6A() {
  const [st, setSt] = useState(0), r = useMemo(() => rng(9), [])
  const steps = ['Perch 1536-D', 'Projection', 'Bi-SSM', 'Attention', 'Prototypes']
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-1.5 items-center">{steps.map((s, i) => <span key={s} className="flex items-center gap-1.5"><Node color={st === i ? C.y : '#fff'} on={st === i} onClick={() => setSt(i)}>{s}</Node>{i < 4 && <span className="text-white mono">›</span>}</span>)}</div>
      <div className="border-[3px] border-black bg-white/5 p-3 min-h-[170px]">
        {st === 0 && <><Cap>One 1536-D vector per window, 12 in a row.</Cap><div className="flex gap-1 mt-2">{Array.from({ length: 12 }, (_, i) => <motion.div key={i} initial={{ y: 14, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: i * 0.04 }} className="flex-1 h-24 border-2 border-black" style={{ background: `linear-gradient(${cm(60 + ((i * 37) % 160))},${cm(200 - ((i * 23) % 120))})` }} />)}</div></>}
        {st === 1 && <><Cap>Embeddings are projected to a smaller size, then get a position code and the recording’s site and hour.</Cap><div className="flex flex-wrap gap-2 mt-3 items-center"><Node color={C.b}>1536 → 256</Node><span className="text-white">+</span><Node color={C.y}>position</Node><span className="text-white">+</span><Node color={C.g}>site</Node><span className="text-white">+</span><Node color={C.r}>hour</Node></div></>}
        {st === 2 && <><Cap>A state-space model reads the 12 windows forward and backward so each window knows its neighbours.</Cap><div className="flex gap-1 mt-3">{Array.from({ length: 12 }, (_, i) => <div key={i} className="flex-1 h-9 border-2 border-black text-black text-[10px] font-bold flex items-center justify-center" style={{ background: C.b }}>{i + 1}</div>)}</div>{['→', '←'].map((d, k) => <motion.div key={d} animate={{ x: k ? [8, -8] : [-8, 8] }} transition={{ repeat: Infinity, repeatType: 'reverse', duration: 1.4 }} className="mono text-center font-bold" style={{ color: k ? C.r : C.y }}>{d.repeat(14)}</motion.div>)}</>}
        {st === 3 && <><Cap>Every window can look at every other window (brighter = pays more attention).</Cap><div className="grid gap-[2px] mt-2 mx-auto w-44" style={{ gridTemplateColumns: 'repeat(12,1fr)' }}>{Array.from({ length: 144 }, (_, k) => { const d = Math.abs((k % 12) - Math.floor(k / 12)); return <motion.div key={k} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: k * 0.003 }} className="aspect-square" style={{ background: cm(255 * Math.exp(-d / 3) * (0.6 + 0.4 * r())) }} /> })}</div></>}
        {st === 4 && <><Cap>Each of the 234 species has a learnable prototype. A window is scored by how close it sits to each one.</Cap><div className="relative h-32 mt-2">{Array.from({ length: 5 }, (_, i) => <motion.div key={i} animate={{ scale: [1, 1.25, 1] }} transition={{ repeat: Infinity, duration: 2, delay: i * 0.3 }} className="absolute w-5 h-5 border-[3px] border-black rotate-45" style={{ left: `${12 + i * 19}%`, top: `${20 + ((i * 37) % 55)}%`, background: [C.y, C.b, C.r, C.g, C.p][i] }} />)}{Array.from({ length: 12 }, (_, i) => <div key={i} className="absolute w-2.5 h-2.5 rounded-full bg-white" style={{ left: `${10 + i * 7}%`, top: `${25 + ((i * 53) % 55)}%` }} />)}</div></>}
      </div>
    </div>
  )
}
function S6B() {
  const [s, setS] = useState(0)
  const proto = col('proto', s), mlp = col('mlp', s), first = proto.map((p, i) => 0.5 * p + 0.5 * mlp[i]), res = col('residual', s)
  return (
    <div className="space-y-2">
      <SpeciesPick s={s} setS={setS} />
      {[['ProtoSSM', proto, C.b], ['MLP on Perch scores', mlp, C.y], ['First pass (50/50)', first, C.g], ['After ResidualSSM', res, C.r]].map(([n, v, c]) => <div key={n}><Cap>{n}</Cap><Bars vals={v} color={c} h={34} lit={(i) => i < NW} /></div>)}
      <Cap>ResidualSSM learns the first pass’s mistakes and nudges each window’s score.</Cap>
    </div>
  )
}
function S6C() {
  const [s, setS] = useState(0), e = col('sed', s), sm = e.map((v, i) => 0.25 * (e[i - 1] ?? v) + 0.5 * v + 0.25 * (e[i + 1] ?? v))
  return (
    <div className="space-y-2">
      <Spec className="h-16 border-[3px] border-black" />
      <SpeciesPick s={s} setS={setS} />
      <div className="grid grid-cols-5 gap-1">{[0, 1, 2, 3, 4].map((f) => <div key={f}><Cap>fold {f + 1}</Cap><Bars vals={e.map((v, i) => Math.min(1, Math.max(0, v + (rng(f * 13 + i + 1)() - 0.5) * 0.14)))} color={C.p} h={34} lit={(i) => i < NW} /></div>)}</div>
      <Cap>Average of 5 folds, then temporal smoothing</Cap>
      <Bars vals={sm} color={C.g} h={44} lit={(i) => i < NW} />
    </div>
  )
}
function BlendList({ w, dark }) {
  const list = blend(w)
  return <div className="space-y-1.5">{list.map((s, i) => <motion.div layout key={s.code} transition={{ type: 'spring', stiffness: 260, damping: 26 }} className="flex items-center gap-2 border-[3px] border-black px-2 py-1 text-black" style={{ background: i === 0 ? C.y : '#fff' }}><b className="mono w-5">{i + 1}</b><span className="font-bold text-sm flex-1">{s.common_name}</span><span className="mono text-[10px]">proto {s.p.toFixed(2)} · sed {s.e.toFixed(2)}</span><div className="w-20 h-3 border-2 border-black bg-white"><motion.div animate={{ width: `${s.score * 100}%` }} className="h-full" style={{ background: C.b }} /></div></motion.div>)}</div>
}
function S7() {
  const [w, setW] = useState(0.6)
  return <div className="space-y-2"><Cap>Each branch’s scores become ranks, then 60% Proto + 40% SED.</Cap><input type="range" min="0" max="1" step="0.1" value={w} onChange={(e) => setW(+e.target.value)} className="w-full accent-[#FDB900]" /><Cap>{Math.round(w * 100)}% Proto / {Math.round((1 - w) * 100)}% SED</Cap><BlendList w={w} /></div>
}
const POST = [['Temperature scaling', (x) => x.map((p) => prob(p, 1.4)), 'Softens over-confident scores.'], ['File-confidence scaling', (x) => { const m = Math.max(...x); return x.map((p) => p * (0.6 + 0.4 * m)) }, 'Scores scale with how sure the file is overall.'], ['Adaptive temporal smoothing', (x) => x.map((p, i) => 0.25 * (x[i - 1] ?? p) + 0.5 * p + 0.25 * (x[i + 1] ?? p)), 'Neighbouring windows share evidence.'], ['Probability clipping', (x) => x.map((p) => Math.min(0.99, Math.max(0.01, p))), 'Keeps scores away from exact 0 and 1.'], ['Per-class thresholds', (x) => x.map((p) => (p >= 0.5 ? p : 0)), 'Below the species’ threshold means no detection.']]
function S8() {
  const [st, setSt] = useState(0), [s, setS] = useState(0)
  let before = col('final', s); for (let i = 0; i < st; i++) before = POST[i][1](before)
  const after = POST[st][1](before)
  return <div className="space-y-2"><Tabs items={POST.map((p, i) => `${i + 1} ${p[0].split(' ')[0]}`)} v={st} set={setSt} color={C.p} /><SpeciesPick s={s} setS={setS} /><Cap>Before</Cap><Bars vals={before} color={C.b} h={44} lit={(i) => i < NW} /><Cap>After · {POST[st][0]}: {POST[st][2]}</Cap><Bars vals={after} color={C.g} h={44} lit={(i) => i < NW} /></div>
}
function S9() {
  return <div className="space-y-2"><Cap>Validation metrics. Add your numbers to EVAL_METRICS at the top of this file.</Cap>{Object.entries(EVAL_METRICS).map(([k, v]) => <div key={k} className="flex items-center gap-2"><span className="mono text-[11px] text-white w-20">{k}</span><div className="flex-1 h-5 border-[3px] border-black bg-white"><motion.div initial={{ width: 0 }} animate={{ width: `${(v ?? 0) * 100}%` }} className="h-full" style={{ background: C.g }} /></div><span className="mono text-[11px] text-white w-10">{v == null ? '—' : v.toFixed(2)}</span></div>)}<div className="grid grid-cols-2 gap-2 pt-1">{['Per-class and overall scores', 'In-distribution vs out-of-distribution'].map((t) => <div key={t} className="border-[3px] border-dashed border-white/50 p-2 mono text-[10px] text-white/80">{t}</div>)}</div></div>
}
function S10() {
  return <div className="space-y-2"><div className="grid grid-cols-3 gap-2">{demoData.top_species.slice(0, 3).map((s, i) => <motion.div key={s.code} initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: i * 0.12 }} className="border-[3px] border-black bg-white p-2 text-black"><span className="mono text-[10px]" style={{ color: C.b }}>#{i + 1}</span><b className="block text-sm leading-tight">{s.common_name}</b><i className="text-[10px]">{s.scientific_name}</i><div className="mono text-[10px] mt-1">max {s.max_score} · {s.seconds_present}s</div></motion.div>)}</div><div className="grid grid-cols-12 gap-[2px]">{demoData.windows.slice(0, 12).map((w) => <div key={w.index} className="h-10 border-2 border-black" title={w.top_k[0]?.common_name} style={{ background: w.is_padding ? '#444' : cm((w.top_k[0]?.score ?? 0) * 255) }} />)}</div><Cap>Per-species cards plus one cell per 5-second window.</Cap><Link to="/analyze" className={`${BTN} inline-block bg-[#FDB900] text-black px-3 py-1.5 text-sm`}>Analyze your own clip</Link></div>
}
function S11() {
  const bx = [['React + Vite', C.y], ['FastAPI', C.b], ['Perch · ProtoSSM · SED', C.r], ['MySQL + audio storage', C.g]]
  return <div className="space-y-3"><div className="flex flex-wrap items-center gap-2">{bx.map(([t, c], i) => <span key={t} className="flex items-center gap-2"><motion.div whileHover={{ y: -4 }} className="border-[3px] border-black px-3 py-3 text-black font-bold text-sm shadow-[4px_4px_0_#fff]" style={{ background: c }}>{t}</motion.div>{i < 3 && <Arrow />}</span>)}</div><Cap>Upload → job queue with progress → models run one at a time → results saved to your history.</Cap></div>
}
const CH = [
  { t: 'Data acquisition', s: '1', c: C.y, S: S1, say: 'The model learns from field recordings of many species: weakly labelled .ogg files, several species per clip, and a very uneven number of examples per species.' },
  { t: 'Audio preprocessing', s: '2', c: C.b, S: S2, say: 'Every recording is converted to the same shape: 32 kHz mono, padded or cut to 60 seconds, then divided into twelve 5-second windows.' },
  { t: 'Perch features', s: '3', c: C.r, S: S3, say: 'Google’s Perch model turns each window into 1536 numbers describing what it sounds like, and also guesses species directly.' },
  { t: 'Extra features', s: '4', c: C.g, S: S4, say: 'Birds call across window edges, so we add neighbour context, simple statistics and a 64-number PCA summary.' },
  { t: 'Augmentation', s: '5', c: C.p, S: S5, say: 'During training only, clips are mixed, noised and masked so the model copes with messy real-world audio.' },
  { t: 'ProtoSSM branch', s: '6.1', c: C.y, S: S6A, say: 'A sequence model reads all 12 windows together, lets them attend to each other, and scores species against learned prototypes.' },
  { t: 'MLP + ResidualSSM', s: '6.1', c: C.b, S: S6B, say: 'An MLP refines Perch’s own scores, the two are averaged, and ResidualSSM corrects what is still wrong.' },
  { t: 'SED branch', s: '6.2', c: C.r, S: S6C, say: 'A separate network listens to the mel spectrogram. Five folds vote, and the result is smoothed over time.' },
  { t: 'Score fusion', s: '7', c: C.g, S: S7, say: 'The two branches are compared by rank, not raw score, and blended 60/40 so neither dominates.' },
  { t: 'Post-processing', s: '8', c: C.p, S: S8, say: 'Five clean-up steps turn blended scores into trustworthy probabilities and decide which detections survive.' },
  { t: 'Evaluation', s: '9', c: C.y, S: S9, say: 'Validation checks the model on unseen recordings, per species and overall, including conditions it was not trained on.' },
  { t: 'Final output', s: '10', c: C.b, S: S10, say: 'You get species, confidence, scientific names and what was heard in each 5-second window.' },
  { t: 'Deployment', s: '11', c: C.r, S: S11, say: 'The whole pipeline runs behind an API so clips can be uploaded, processed in the background and revisited from your history.' },
]

function TV() {
  const [ch, setCh] = useState(0), [noise, setNoise] = useState(false)
  const go = (n) => { const k = (n + CH.length) % CH.length; if (k === ch) return; setNoise(true); setCh(k); setTimeout(() => setNoise(false), 380) }
  const { t, s, c, S, say } = CH[ch]
  return (
    <div tabIndex={0} onKeyDown={(e) => (e.key === 'ArrowRight' ? go(ch + 1) : e.key === 'ArrowLeft' && go(ch - 1))} className="outline-none">
      <div className="relative mx-auto max-w-5xl pt-14">
        {[-1, 1].map((d) => <motion.div key={d} initial={{ rotate: 0 }} animate={{ rotate: d * 28 }} transition={{ type: 'spring', delay: 0.3 }} className="absolute top-0 left-1/2 h-20 w-1.5 bg-black origin-bottom" style={{ marginLeft: d * 14 }} />)}
        <div className={`${BOX} relative grid gap-4 p-4 md:grid-cols-[1fr_190px] rounded-[28px] shadow-[10px_10px_0_#000]`} style={{ background: C.b }}>
          <div className="rounded-[20px] border-[4px] border-black bg-black p-2">
            <div className="relative h-[480px] overflow-hidden rounded-[14px]" style={{ background: '#101418', animation: 'hiw-flick .2s infinite' }}>
              <div className="absolute inset-0 z-20 pointer-events-none" style={{ background: 'repeating-linear-gradient(0deg,rgba(0,0,0,.18) 0 1px,transparent 1px 3px),radial-gradient(ellipse at center,transparent 60%,rgba(0,0,0,.55))' }} />
              <AnimatePresence>{noise && <motion.div key="n" initial={{ opacity: 1 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.15 }} className="absolute inset-0 z-30" style={{ backgroundImage: NOISE, backgroundSize: '160px', animation: 'hiw-noise .12s steps(4) infinite', filter: 'grayscale(1) contrast(1.6)' }} />}</AnimatePresence>
              <div className="absolute right-3 top-2 z-20 mono text-xl font-bold" style={{ color: '#4ade80', textShadow: '0 0 8px #4ade80' }}>CH {String(ch + 1).padStart(2, '0')}</div>
              <div className="absolute inset-x-0 bottom-0 z-20 flex items-center gap-2 px-3 py-1.5 text-black font-bold text-sm border-t-[3px] border-black" style={{ background: c }}><Chip>stage {s}</Chip>{t}</div>
              <div className="relative h-full overflow-y-auto px-4 pt-9 pb-12 text-white">
                <AnimatePresence mode="wait"><motion.div key={ch} initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} transition={{ delay: 0.2, duration: 0.25 }}><S /></motion.div></AnimatePresence>
              </div>
            </div>
          </div>
          <div className="flex flex-row items-center gap-4 md:flex-col md:justify-between">
            <motion.div animate={{ rotate: ch * (360 / CH.length) }} transition={{ type: 'spring', stiffness: 90 }} className="h-16 w-16 shrink-0 rounded-full border-[3px] border-black bg-[#FDB900] shadow-[4px_4px_0_#000] relative"><span className="absolute left-1/2 top-1 h-6 w-1.5 -translate-x-1/2 bg-black" /></motion.div>
            <div className="grid grid-cols-5 gap-1.5 md:grid-cols-4">{CH.map((x, i) => <button key={i} onClick={() => go(i)} aria-label={`Channel ${i + 1}: ${x.t}`} className={`mono h-8 border-[3px] border-black text-[11px] font-bold text-black transition-all ${i === ch ? 'translate-x-[2px] translate-y-[2px]' : 'shadow-[3px_3px_0_#000]'}`} style={{ background: i === ch ? x.c : '#fff' }}>{i + 1}</button>)}</div>
            <div className="hidden h-20 w-full border-[3px] border-black md:block" style={{ background: 'repeating-linear-gradient(90deg,#000 0 3px,#FDB900 3px 9px)' }} />
          </div>
        </div>
        <div className="mx-auto flex max-w-3xl justify-between px-10"><span className="h-5 w-8 bg-black" /><span className="h-5 w-8 bg-black" /></div>
      </div>
      <div className="mx-auto mt-6 grid max-w-5xl items-stretch gap-4 md:grid-cols-[auto_1fr_auto]">
        <button onClick={() => go(ch - 1)} className={`${BTN} bg-white px-6 py-3 text-lg text-black`}>◀ Previous</button>
        <AnimatePresence mode="wait"><motion.div key={ch} initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ opacity: 0 }} className={`${BOX} bg-white p-3 text-black`}><Chip color={c} text="#000">channel {ch + 1} of {CH.length}</Chip><p className="mt-1 text-sm leading-snug"><b>{t}.</b> {say}</p></motion.div></AnimatePresence>
        <button onClick={() => go(ch + 1)} className={`${BTN} px-6 py-3 text-lg text-black`} style={{ background: C.g }}>Next ▶</button>
      </div>
    </div>
  )
}

/* ───────── sections (same content as before, restyled) ───────── */
const Sec = ({ id, bg = '#fff', dark, label, labelColor = C.p, title, children }) => (
  <section id={id} className="border-b-[3px] border-black py-16" style={{ background: bg, color: dark ? '#fff' : '#000' }}>
    <div className="mx-auto max-w-6xl px-4 sm:px-6">
      <Chip color={labelColor} text={labelColor === C.y ? '#000' : '#fff'}>{label}</Chip>
      <h2 className="mb-8 mt-3 max-w-3xl text-4xl font-bold leading-[1.05] tracking-tight md:text-5xl">{title}</h2>
      {children}
    </div>
  </section>
)
const STEPS = [['Audio input', '60-second recording at 32 kHz', 'Raw mono audio loaded from file'], ['Preprocessing', 'Split into 12 consecutive 5-second windows', 'Normalize amplitude, apply padding'], ['Perch embeddings', 'Bird-specific audio representations', 'Extract 1536-dim embeddings per window'], ['Multi-branch detection', 'Parallel inference across branches', 'ProtoSSM, MLP, ResidualSSM, SED ensemble'], ['Rank blend', 'Combine scores with learned weights', '0.6 × Proto + 0.4 × SED (configurable)'], ['Post-processing', 'Apply temperature & threshold filtering', 'Smooth predictions over time'], ['Results', 'Per-window & aggregate predictions', 'Species rankings with confidence scores']]
const COLS = [C.y, C.b, C.r, C.g, C.p, C.y, C.b]

function Pipeline() {
  const [a, setA] = useState(0)
  return (
    <Sec id="pipeline-section" label="1 · pipeline" labelColor={C.b} title="Seven steps from sound to species.">
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-3">{STEPS.map(([t, d], i) => <motion.button key={t} whileHover={{ x: 6 }} onClick={() => setA(i)} className={`${BTN} flex w-full items-center gap-3 p-3 text-left`} style={{ background: a === i ? COLS[i] : '#fff' }}><span className="mono flex h-8 w-8 items-center justify-center border-[3px] border-black bg-black text-white">{i + 1}</span><span><b className="block">{t}</b><span className="text-sm">{d}</span></span></motion.button>)}</div>
        <AnimatePresence mode="wait"><motion.div key={a} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }} className={`${BOX} h-fit bg-black p-6 text-white lg:sticky lg:top-28`}><Chip color={COLS[a]} text="#000">step {a + 1}</Chip><h3 className="mt-3 text-3xl font-bold">{STEPS[a][0]}</h3><p className="mt-2 text-white/80">{STEPS[a][1]}</p><div className="mono mt-4 border-[3px] border-white/40 p-3 text-sm">{STEPS[a][2]}</div></motion.div></AnimatePresence>
      </div>
    </Sec>
  )
}
function Windowing() {
  const [play, setPlay] = useState(true), [pad, setPad] = useState(true)
  return (
    <Sec id="windowing-section" bg={C.y} label="2 · windowing" labelColor="#000" title="60 seconds become 12 windows of 5.">
      <div className={`${BOX} bg-white p-6`}>
        <div className="mb-5 flex gap-2"><button onClick={() => setPlay(!play)} className={`${BTN} bg-black px-4 py-2 text-white`}>{play ? 'Pause' : 'Play'} animation</button><button onClick={() => setPad(!pad)} className={`${BTN} bg-white px-4 py-2`}>{pad ? 'Showing short clip (padded)' : 'Showing full 60 s clip'}</button></div>
        <div className="mono mb-1 text-xs">Recording · {pad ? `${DUR.toFixed(1)} s + padding` : '60 s'}</div>
        <div className="relative flex h-16 border-[3px] border-black" style={{ background: 'repeating-linear-gradient(45deg,#ddd 0 6px,#fff 6px 12px)' }}><motion.div animate={play ? { scaleX: [0, 1] } : { scaleX: 1 }} transition={{ duration: 3, repeat: Infinity }} className="h-full origin-left border-r-[3px] border-black" style={{ width: `${pad ? (DUR / 60) * 100 : 100}%`, background: C.b }} /></div>
        <div className="my-3 text-center text-2xl">↓</div>
        <div className="grid grid-cols-6 gap-2 md:grid-cols-12">{Array.from({ length: 12 }, (_, i) => <motion.div key={i} animate={play ? { y: [0, -6, 0] } : {}} transition={{ repeat: Infinity, duration: 1.6, delay: i * 0.08 }} className="mono flex aspect-square items-center justify-center border-[3px] border-black font-bold" style={{ background: !pad || i < NW ? COLS[i % 5] : '#ddd', color: '#000' }}>{i + 1}</motion.div>)}</div>
        <p className="mt-4 text-sm">Each window goes through the model on its own; results are combined afterwards.</p>
      </div>
    </Sec>
  )
}
function Waveform() {
  const [h, setH] = useState(null)
  return (
    <Sec id="waveform-section" dark bg={C.k} label="3 · waveform" labelColor={C.g} title="Hover the waveform to see what each window heard.">
      <div className="relative border-[3px] border-white bg-[#101418] p-4" onMouseLeave={() => setH(null)}>
        <div className="relative flex h-56 items-center gap-[2px]">
          {PEAKS.map((p, i) => <motion.div key={i} initial={{ height: 0 }} animate={{ height: `${Math.max(3, p * 100)}%` }} transition={{ delay: i * 0.006 }} className="flex-1" style={{ background: C.b }} />)}
          <div className="absolute inset-0 flex">{Array.from({ length: 12 }, (_, i) => <div key={i} onMouseEnter={() => setH(i)} className="flex-1 border-l-2 border-white/30 transition-colors" style={{ background: h === i ? `${COLS[i % 5]}66` : i >= NW ? 'repeating-linear-gradient(45deg,#ffffff22 0 4px,transparent 4px 8px)' : 'transparent', width: `${100 / 12}%` }} />)}</div>
        </div>
        <AnimatePresence>{h != null && <motion.div key={h} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="absolute top-2 border-[3px] border-black bg-white p-2 text-black shadow-[4px_4px_0_#000]" style={{ left: `clamp(4px,${(h / 12) * 100}%,calc(100% - 200px))` }}><div className="mono text-[10px] font-bold">{h * 5}s – {h * 5 + 5}s</div>{h >= NW ? <div className="text-sm">padding (no audio)</div> : (demoData.windows[h]?.top_k ?? []).slice(0, 3).map((k) => <div key={k.code} className="flex justify-between gap-3 text-sm"><b>{k.common_name}</b><span className="mono">{k.score.toFixed(2)}</span></div>)}</motion.div>}</AnimatePresence>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">{['12 non-overlapping 5-second windows (hatched = padding)', 'Each window is analyzed independently'].map((t) => <div key={t} className="mono border-[3px] border-white/60 p-3 text-sm">{t}</div>)}</div>
    </Sec>
  )
}
const TIP = { backgroundColor: '#fff', border: '3px solid #000', borderRadius: 0, color: '#000' }
function Branches() {
  const [s, setS] = useState(0), bs = ['perch', 'proto', 'mlp', 'residual', 'sed', 'final'], cc = [C.b, '#06b6d4', C.y, C.p, '#8b5cf6', C.g]
  const data = Array.from({ length: 12 }, (_, i) => Object.fromEntries([['window', `W${i}`], ...bs.map((b) => [b, BS[b]?.[i]?.[s] ?? 0])]))
  return (
    <Sec id="branch-section" label="4 · branches" labelColor={C.r} title="Same species, six different opinions.">
      <div className={`${BOX} bg-white p-6`}><SpeciesPickLight s={s} setS={setS} /><div className="mt-4"><ResponsiveContainer width="100%" height={380}><BarChart data={data}><CartesianGrid strokeDasharray="3 3" stroke="#000" strokeOpacity={0.2} /><XAxis dataKey="window" stroke="#000" /><YAxis stroke="#000" /><Tooltip contentStyle={TIP} /><Legend />{bs.map((b, i) => <Bar key={b} dataKey={b} fill={cc[i]} stroke="#000" strokeWidth={1.5} />)}</BarChart></ResponsiveContainer></div></div>
    </Sec>
  )
}
const SpeciesPickLight = SpeciesPick
function Blending() {
  const [w, setW] = useState(0.6)
  return (
    <Sec id="blend-section" bg={C.g} label="5 · blending" labelColor="#000" title="Move the slider and watch the ranking reshuffle.">
      <div className={`${BOX} bg-white p-6`}>
        <div className="mono mb-2 flex justify-between text-sm font-bold"><span>Proto weight vs SED weight</span><span>{Math.round(w * 100)}% / {Math.round((1 - w) * 100)}%</span></div>
        <input type="range" min="0" max="1" step="0.1" value={w} onChange={(e) => setW(+e.target.value)} className="mb-2 w-full accent-black" />
        <div className="mono mb-5 text-xs">Formula: {w.toFixed(1)} × rank(Proto) + {(1 - w).toFixed(1)} × rank(SED)</div>
        <BlendList w={w} />
      </div>
    </Sec>
  )
}
function Thresholds() {
  const [T, setT] = useState(1), [th, setTh] = useState(0.5)
  const rows = demoData.top_species.slice(0, 5).map((s) => ({ name: s.common_name, p: +prob(s.mean_score, T).toFixed(3) }))
  return (
    <Sec id="threshold-section" bg={C.p} dark label="6 · tuning" labelColor="#000" title="Temperature softens. Thresholds decide.">
      <div className="grid gap-6 lg:grid-cols-2">
        <div className={`${BOX} space-y-8 bg-white p-6 text-black`}>
          <div><label className="mono mb-2 block text-sm font-bold">Temperature {T.toFixed(1)}</label><input type="range" min="0.2" max="2" step="0.1" value={T} onChange={(e) => setT(+e.target.value)} className="w-full accent-black" /><p className="mt-1 text-xs">Lower = sharper · higher = softer</p></div>
          <div><label className="mono mb-2 block text-sm font-bold">Threshold {Math.round(th * 100)}%</label><input type="range" min="0" max="1" step="0.05" value={th} onChange={(e) => setTh(+e.target.value)} className="w-full accent-black" /><p className="mt-1 text-xs">Species below this line are dropped.</p></div>
          {rows.map((r) => <div key={r.name} className="flex justify-between text-sm"><b>{r.name}</b><Chip color={r.p >= th ? C.g : C.r}>{r.p >= th ? 'pass' : 'fail'}</Chip></div>)}
        </div>
        <div className={`${BOX} bg-white p-4 text-black`}><ResponsiveContainer width="100%" height={320}><BarChart data={rows}><CartesianGrid strokeDasharray="3 3" stroke="#000" strokeOpacity={0.2} /><XAxis dataKey="name" stroke="#000" angle={-30} textAnchor="end" height={70} interval={0} tick={{ fontSize: 11 }} /><YAxis domain={[0, 1]} stroke="#000" /><Tooltip contentStyle={TIP} /><ReferenceLine y={th} stroke={C.r} strokeWidth={3} strokeDasharray="6 4" /><Bar dataKey="p" fill={C.b} stroke="#000" strokeWidth={2} /></BarChart></ResponsiveContainer></div>
      </div>
    </Sec>
  )
}
function Heatmap() {
  const { species, matrix } = demoData.heatmap, level = (v) => (v < 0.3 ? 40 : v < 0.5 ? 90 : v < 0.7 ? 150 : v < 0.85 ? 200 : 250)
  return (
    <Sec id="heatmap-section" bg={C.k} dark label="7 · heatmap" labelColor={C.y} title="Every species, every 5 seconds.">
      <div className="overflow-x-auto border-[3px] border-white bg-[#101418] p-4">
        <table className="w-full min-w-[640px] border-separate border-spacing-1 text-sm">
          <thead><tr><th className="text-left">Species</th>{Array.from({ length: 12 }, (_, i) => <th key={i} className="mono text-xs">W{i}</th>)}</tr></thead>
          <tbody>{species.map((sp, r) => <tr key={sp.code}><td className="whitespace-nowrap pr-3 font-bold">{sp.common_name}</td>{matrix[r].map((v, i) => <motion.td key={i} initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ delay: i * 0.03 }} title={`${sp.common_name} · window ${i}: ${(v * 100).toFixed(0)}%`} className="mono border-2 border-black py-1.5 text-center text-xs font-bold" style={{ background: cm(level(v)), color: level(v) > 150 ? '#000' : '#fff' }}>{Math.round(v * 100)}</motion.td>)}</tr>)}</tbody>
        </table>
        <div className="mono mt-4 flex flex-wrap gap-3 text-xs">{[['<30%', 40], ['30–50%', 90], ['50–70%', 150], ['70–85%', 200], ['>85%', 250]].map(([t, v]) => <span key={t} className="flex items-center gap-1.5"><i className="inline-block h-4 w-4 border-2 border-white" style={{ background: cm(v) }} />{t}</span>)}</div>
      </div>
    </Sec>
  )
}

/* ───────── page ───────── */
const SECTIONS = [['tv-section', 'TV tour'], ['pipeline-section', 'Pipeline'], ['windowing-section', 'Windowing'], ['waveform-section', 'Waveform'], ['branch-section', 'Branches'], ['blend-section', 'Blending'], ['threshold-section', 'Thresholds'], ['heatmap-section', 'Heatmap']]
const TOUR = [['#tv-section', 'Flip through 13 channels: one per stage of the pipeline.'], ['#pipeline-section', 'The whole pipeline at a glance.'], ['#windowing-section', 'How audio is cut into 5-second windows.'], ['#waveform-section', 'Hover the waveform to see detections per window.'], ['#branch-section', 'Compare what each branch thinks.'], ['#blend-section', 'Change the blend weight and watch the ranking move.'], ['#threshold-section', 'Tune temperature and threshold.'], ['#heatmap-section', 'The full species-by-time picture.']].map(([target, content]) => ({ target, content, placement: 'bottom', disableBeacon: true }))

export default function HowItWorks() {
  const [run, setRun] = useState(false), [act, setAct] = useState(0)
  useEffect(() => {
    const f = () => { let k = 0; SECTIONS.forEach(([id], i) => { const e = document.getElementById(id); if (e && window.scrollY + 220 >= e.offsetTop) k = i }); setAct(k) }
    window.addEventListener('scroll', f); return () => window.removeEventListener('scroll', f)
  }, [])
  return (
    <div className="hiw min-h-screen overflow-x-hidden bg-white text-black">
      <style>{CSS}</style>
      <Joyride steps={TOUR} run={run} continuous showSkip scrollToFirstStep callback={(d) => ['finished', 'skipped'].includes(d.status) && setRun(false)} styles={{ options: { primaryColor: C.y, textColor: '#000', backgroundColor: '#fff', arrowColor: '#000', zIndex: 10000 }, tooltip: { border: '3px solid #000', borderRadius: 0, boxShadow: '6px 6px 0 #000' }, buttonNext: { color: '#000', borderRadius: 0, border: '3px solid #000', fontWeight: 700 } }} />
      <header className="border-b-[3px] border-black px-4 py-12 sm:px-6">
        <div className="mx-auto flex max-w-6xl flex-wrap items-end justify-between gap-6 border-l-[6px] pl-5" style={{ borderColor: C.p }}>
          <div className="max-w-2xl"><span className="mono text-[11px] font-bold tracking-wider text-black/60">INTERACTIVE · PIPELINE · GUIDED TOUR</span><h1 className="mt-2 text-5xl font-bold tracking-tight md:text-6xl">How it works</h1><p className="mt-3 text-black/70">Follow one recording from raw sound to species predictions: flip the channels, then play with the parts below.</p></div>
          <button onClick={() => setRun(true)} className={`${BTN} px-5 py-3 text-black`} style={{ background: C.y }}>Take the guided tour</button>
        </div>
      </header>
      <nav className="sticky top-0 z-40 overflow-x-auto border-b-[3px] border-black bg-white"><div className="mx-auto flex max-w-6xl gap-2 px-4 py-2 sm:px-6">{SECTIONS.map(([id, n], i) => <button key={id} onClick={() => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })} className="mono whitespace-nowrap border-2 border-black px-3 py-1 text-xs font-bold" style={{ background: act === i ? C.y : '#fff' }}>{n}</button>)}</div></nav>
      <section id="tv-section" className="border-b-[3px] border-black px-4 py-16 sm:px-6" style={{ background: C.y }}>
        <div className="mx-auto mb-8 max-w-5xl"><Chip>watch the pipeline</Chip><h2 className="mt-3 max-w-3xl text-4xl font-bold leading-[1.05] tracking-tight md:text-5xl">One recording, thirteen channels.</h2><p className="mt-2 text-black/75">Use Next and Previous, the number keypad or your arrow keys. The audio you see is the real demo clip; model scores are demo data.</p></div>
        <TV />
      </section>
      <Pipeline /><Windowing /><Waveform /><Branches /><Blending /><Thresholds /><Heatmap />
      <section className="px-4 py-16 sm:px-6" style={{ background: C.p }}>
        <div className={`${BOX} mx-auto grid max-w-6xl gap-6 bg-black p-8 text-white md:grid-cols-[1fr_auto] md:items-center`}>
          <div><h2 className="text-4xl font-bold leading-tight md:text-5xl">The pipeline is real. Try it on your own recording.</h2><p className="mt-2 text-white/70">Upload a clip and get the same per-window breakdown for your own audio.</p></div>
          <div className="flex flex-col gap-3"><Link to="/analyze" className={`${BTN} px-6 py-3 text-center text-black`} style={{ background: C.g }}>Analyze a clip</Link><button onClick={() => { window.scrollTo({ top: 0, behavior: 'smooth' }); setRun(true) }} className={`${BTN} px-6 py-3 text-black`} style={{ background: C.y }}>Replay the tour</button></div>
        </div>
      </section>
    </div>
  )
}