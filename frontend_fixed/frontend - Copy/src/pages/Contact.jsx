import { useState } from 'react'
import { motion } from 'framer-motion'

export default function Contact() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  })
  const [status, setStatus] = useState('idle') // idle, loading, success, error
  const [errorMessage, setErrorMessage] = useState('')

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setStatus('loading')
    setErrorMessage('')

    const endpoint = import.meta.env.VITE_CONTACT_ENDPOINT

    if (!endpoint) {
      // Fallback: open mailto link
      const mailtoLink = `mailto:contact@example.com?subject=${encodeURIComponent(formData.subject)}&body=${encodeURIComponent(formData.message)}`
      window.location.href = mailtoLink
      setStatus('success')
      return
    }

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        setStatus('success')
        setFormData({ name: '', email: '', subject: '', message: '' })
        setTimeout(() => setStatus('idle'), 5000)
      } else {
        throw new Error('Failed to send message')
      }
    } catch (error) {
      setStatus('error')
      setErrorMessage(error.message || 'Failed to send message. Please try again.')
      setTimeout(() => setStatus('idle'), 5000)
    }
  }

  return (
    <div className="min-h-screen bg-[#fff8e8] text-[#171717] overflow-hidden">
      <section className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 border-2 border-black bg-[#b9e7ff] px-3 py-1.5 shadow-[3px_3px_0_#171717] mb-6">
            <span className="h-2 w-2 rounded-full bg-[#171717]" />
            <span className="font-mono text-xs font-bold uppercase tracking-widest">WildEcho / Contact</span>
          </div>
          <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight mb-6">
            Get in Touch<span className="text-[#f4c542]">.</span>
          </h1>
          <p className="text-lg sm:text-xl text-[#625d53] max-w-2xl mx-auto">
            Have questions about BirdCLEF or want to collaborate? We'd love to hear from you.
          </p>
        </motion.div>

        {/* Contact Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="bg-white border-2 border-black p-6 sm:p-10 shadow-[7px_7px_0_#171717]"
        >
          {status === 'success' && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 bg-[#d9f4d2] border-2 border-black text-[#245c2a] font-semibold shadow-[3px_3px_0_#171717]"
            >
              ✓ Thank you! Your message has been sent successfully. We'll get back to you soon.
            </motion.div>
          )}

          {status === 'error' && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 bg-[#ffe0df] border-2 border-black text-[#9f2424] font-semibold shadow-[3px_3px_0_#171717]"
            >
              ✕ {errorMessage}
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-bold mb-2">
                Name
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-[#fff8e8] border-2 border-black text-[#171717] placeholder-[#aaa398] focus:outline-none focus:ring-2 focus:ring-[#f4c542] transition"
                placeholder="Your name"
              />
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-bold mb-2">
                Email
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-[#fff8e8] border-2 border-black text-[#171717] placeholder-[#aaa398] focus:outline-none focus:ring-2 focus:ring-[#f4c542] transition"
                placeholder="your.email@example.com"
              />
            </div>

            {/* Subject */}
            <div>
              <label htmlFor="subject" className="block text-sm font-bold mb-2">
                Subject
              </label>
              <input
                type="text"
                id="subject"
                name="subject"
                value={formData.subject}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-[#fff8e8] border-2 border-black text-[#171717] placeholder-[#aaa398] focus:outline-none focus:ring-2 focus:ring-[#f4c542] transition"
                placeholder="What's this about?"
              />
            </div>

            {/* Message */}
            <div>
              <label htmlFor="message" className="block text-sm font-bold mb-2">
                Message
              </label>
              <textarea
                id="message"
                name="message"
                value={formData.message}
                onChange={handleChange}
                required
                rows="6"
                className="w-full px-4 py-3 bg-[#fff8e8] border-2 border-black text-[#171717] placeholder-[#aaa398] focus:outline-none focus:ring-2 focus:ring-[#f4c542] transition resize-none"
                placeholder="Tell us what you're thinking..."
              />
            </div>

            {/* Submit Button */}
            <motion.button
              type="submit"
              disabled={status === 'loading'}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full px-6 py-4 bg-[#f4c542] border-2 border-black text-[#171717] font-extrabold uppercase tracking-wide shadow-[4px_4px_0_#171717] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_#171717] disabled:bg-[#e8dfc9] disabled:opacity-70 disabled:cursor-not-allowed transition"
            >
              {status === 'loading' ? 'Sending...' : 'Send Message'}
            </motion.button>
          </form>
        </motion.div>

        {/* Additional Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6"
        >
          <div className="bg-[#b9e7ff] border-2 border-black p-6 shadow-[5px_5px_0_#171717]">
            <div className="font-mono text-[10px] font-bold uppercase tracking-widest mb-3">01 / Support</div>
            <h3 className="text-lg font-extrabold mb-2">Response Time</h3>
            <p className="text-[#3f4c50]">
              We typically respond to inquiries within 24-48 hours during business days.
            </p>
          </div>

          <div className="bg-[#ffcfdb] border-2 border-black p-6 shadow-[5px_5px_0_#171717]">
            <div className="font-mono text-[10px] font-bold uppercase tracking-widest mb-3">02 / Your Data</div>
            <h3 className="text-lg font-extrabold mb-2">Privacy</h3>
            <p className="text-[#59434a]">
              Your information is safe with us. We never share your details with third parties.
            </p>
          </div>
        </motion.div>
      </section>
    </div>
  )
}
