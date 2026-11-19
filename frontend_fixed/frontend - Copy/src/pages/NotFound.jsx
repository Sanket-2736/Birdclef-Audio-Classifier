import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'

export default function NotFound() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-[#fff8e8] text-[#171717] flex items-center justify-center overflow-hidden px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="text-center max-w-2xl"
      >
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="inline-block text-8xl sm:text-9xl font-extrabold leading-none mb-6 bg-[#f4c542] border-2 border-black px-6 py-3 shadow-[8px_8px_0_#171717]"
        >
          404
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4"
        >
          Page Not Found<span className="text-[#e5a7b8]">.</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="text-lg sm:text-xl text-[#625d53] mb-10 max-w-xl mx-auto leading-relaxed"
        >
          The page you're looking for doesn't exist. It might have been moved or removed.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="flex flex-col sm:flex-row gap-5 justify-center"
        >
          <motion.button
            whileHover={{ y: -3, x: -2 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate('/')}
            className="px-8 py-3.5 bg-[#f4c542] border-2 border-black shadow-[5px_5px_0_#171717] hover:shadow-[2px_2px_0_#171717] hover:translate-x-[3px] hover:translate-y-[3px] font-extrabold uppercase tracking-wide transition"
          >
            Return Home
          </motion.button>

          <motion.button
            whileHover={{ y: -3, x: -2 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate('/how-it-works')}
            className="px-8 py-3.5 bg-[#b9e7ff] border-2 border-black shadow-[5px_5px_0_#171717] hover:shadow-[2px_2px_0_#171717] hover:translate-x-[3px] hover:translate-y-[3px] font-extrabold uppercase tracking-wide transition"
          >
            Explore Demo
          </motion.button>
        </motion.div>

        {/* Decorative elements */}
        <motion.div
          animate={{ y: [0, 10, 0], rotate: [0, 5, -5, 0] }}
          transition={{ duration: 3, repeat: Infinity }}
          className="mt-16 inline-flex items-center justify-center w-24 h-24 text-5xl bg-[#d9f4d2] border-2 border-black shadow-[5px_5px_0_#171717]"
        >
          🐦
        </motion.div>
        <p className="mt-7 font-mono text-[10px] uppercase tracking-[0.2em] text-[#8a8378]">
          WildEcho · Bird Audio Intelligence
        </p>
      </motion.div>
    </div>
  )
}
