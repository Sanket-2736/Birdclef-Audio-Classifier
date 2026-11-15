import { useNavigate } from 'react-router-dom'

export default function Footer() {
  const navigate = useNavigate()
  const currentYear = new Date().getFullYear()

  const footerLinks = [
    {
      title: 'Navigation',
      links: [
        { label: 'Home', onClick: () => navigate('/') },
        { label: 'How It Works', onClick: () => navigate('/how-it-works') },
        { label: 'About', onClick: () => navigate('/about') },
        { label: 'Contact', onClick: () => navigate('/contact') }
      ]
    },
    {
      title: 'Resources',
      links: [
        { label: 'BirdCLEF Challenge', href: 'https://www.kaggle.com/competitions/birdclef-2026', external: true },
        { label: 'Cornell Lab of Ornithology', href: 'https://www.birds.cornell.edu/', external: true },
        { label: 'Perch Research', href: 'https://www.google.com/research/', external: true }
      ]
    },
    {
      title: 'Info',
      links: [
        { label: 'Privacy Policy', href: '#', onClick: () => {} },
        { label: 'Terms of Service', href: '#', onClick: () => {} }
      ]
    }
  ]

  return (
    <footer className="bg-navy-950 border-t border-navy-700 text-navy-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Grid Layout */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
          {/* Brand Section */}
          <div className="md:col-span-1">
            <h2 className="text-2xl font-bold text-white mb-2">BirdCLEF</h2>
            <p className="text-sm text-navy-400">
              Advanced audio classification for bird species detection.
            </p>
          </div>

          {/* Links */}
          {footerLinks.map((section, idx) => (
            <div key={idx}>
              <h3 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider">
                {section.title}
              </h3>
              <ul className="space-y-2">
                {section.links.map((link, linkIdx) => (
                  <li key={linkIdx}>
                    {link.external ? (
                      <a
                        href={link.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm hover:text-blue-400 transition"
                      >
                        {link.label}
                      </a>
                    ) : (
                      <button
                        onClick={link.onClick || (() => {})}
                        className="text-sm hover:text-blue-400 transition text-left"
                      >
                        {link.label}
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Divider */}
        <div className="border-t border-navy-700 pt-8">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <p className="text-sm text-navy-400">
              &copy; {currentYear} BirdCLEF Audio Classifier. All rights reserved.
            </p>
            <div className="flex gap-6 text-sm">
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-blue-400 transition"
              >
                GitHub
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-blue-400 transition"
              >
                Twitter
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
