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
    <footer className="bg-[#fff8e8] border-t border-[#171717] text-[#514a40]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Grid Layout */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
          {/* Brand Section */}
          <div className="md:col-span-1">
            <h2 className="text-2xl font-bold text-[#171717] mb-2">WildEcho</h2>
            <p className="text-sm text-[#766d5e]">
              Advanced audio classification for bird species detection.
            </p>
          </div>

          {/* Links */}
          {footerLinks.map((section, idx) => (
            <div key={idx}>
              <h3 className="text-sm font-semibold text-[#171717] mb-4 uppercase tracking-wider">
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
                        className="text-sm hover:text-[#171717] transition"
                      >
                        {link.label}
                      </a>
                    ) : (
                      <button
                        onClick={link.onClick || (() => {})}
                        className="text-sm hover:text-[#171717] border-2 border-[#171717] shadow-[3px_3px_0_#171717] transition hover:translate-x-[1px] hover:translate-y-[1px] text-left"
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
        <div className="border-t border-[#171717] pt-8">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <p className="text-sm text-[#766d5e]">
              &copy; {currentYear} WildEcho · Bird Audio Intelligence. All rights reserved.
            </p>
            <div className="flex gap-6 text-sm">
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-[#171717] transition"
              >
                GitHub
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-[#171717] transition"
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
