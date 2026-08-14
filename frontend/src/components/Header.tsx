import React, { useState, useEffect } from 'react';

interface HeaderProps {
  onNavigateToStudio: () => void;
  onNavigateToHome: () => void;
  activeView: 'home' | 'studio';
}

export const Header: React.FC<HeaderProps> = ({
  onNavigateToStudio,
  onNavigateToHome,
  activeView
}) => {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/health/ping', { method: 'GET' });
        setBackendOnline(res.ok);
      } catch {
        try {
          const res2 = await fetch('http://localhost:8000/docs');
          setBackendOnline(res2.ok);
        } catch {
          setBackendOnline(false);
        }
      }
    };
    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed top-4 left-0 right-0 z-50 flex justify-center px-4">
      <header
        className={`w-full max-w-5xl rounded-full border border-black/15 bg-[#FDFCF0] py-2.5 pl-6 pr-3 shadow-md backdrop-blur-md transition-all duration-300 ${
          scrolled ? 'shadow-lg border-black/25 bg-[#FDFCF0]/95' : ''
        }`}
      >
        <div className="flex items-center justify-between">
          {/* Brand Logo */}
          <button
            onClick={onNavigateToHome}
            className="flex items-center gap-2 group focus:outline-none"
          >
            {/* 3-bar animated soundwave logo */}
            <div className="flex items-end gap-0.5 h-4.5 w-5">
              <span className="w-0.75 bg-[#1A1A1A] rounded-full soundwave-bar" style={{ animationDelay: '0.1s', height: '100%' }} />
              <span className="w-0.75 bg-[#1A1A1A] rounded-full soundwave-bar" style={{ animationDelay: '0.3s', height: '60%' }} />
              <span className="w-0.75 bg-[#1A1A1A] rounded-full soundwave-bar" style={{ animationDelay: '0.2s', height: '80%' }} />
              <span className="w-0.75 bg-[#1A1A1A] rounded-full soundwave-bar" style={{ animationDelay: '0.4s', height: '50%' }} />
            </div>
            <span className="font-['Outfit',sans-serif] font-bold text-xl text-[#1A1A1A] tracking-tight">
              Flow
            </span>
            {/* Tiny backend status dot */}
            <span
              className={`ml-1 h-2 w-2 rounded-full transition-colors ${
                backendOnline === null ? 'bg-amber-400' : backendOnline ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-red-500'
              }`}
              title={backendOnline ? "Backend Connected (FastAPI)" : "Offline (Preset Mode)"}
            />
          </button>

          {/* Center Tabs */}
          <div className="flex items-center gap-1 bg-[#F4F3E8] p-1 rounded-full border border-black/5">
            <button
              onClick={onNavigateToHome}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold tracking-wide transition-all ${
                activeView === 'home'
                  ? 'bg-white text-[#1A1A1A] shadow-xs'
                  : 'text-[#8A8A8A] hover:text-[#1A1A1A]'
              }`}
            >
              Overview
            </button>
            <button
              onClick={onNavigateToStudio}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold tracking-wide transition-all flex items-center gap-1.5 ${
                activeView === 'studio'
                  ? 'bg-white text-[#1A1A1A] shadow-xs'
                  : 'text-[#8A8A8A] hover:text-[#1A1A1A]'
              }`}
            >
              Video Studio
              <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded-full bg-[#D9CCF5] text-[#1a1a1a]">
                AI
              </span>
            </button>
          </div>

          {/* Right Links & CTA */}
          <div className="flex items-center gap-6">
            <nav className="hidden md:flex items-center gap-5 text-xs font-bold uppercase tracking-wider text-[#1A1A1A]/70">
              <a href="#playground" className="hover:text-[#1A1A1A] transition-colors">
                Dictation Lab
              </a>
              <a href="#features" className="hover:text-[#1A1A1A] transition-colors">
                Features
              </a>
            </nav>

            {/* CTA Button */}
            <button
              onClick={onNavigateToStudio}
              className="flex items-center gap-2 rounded-full bg-[#E5D7FA] hover:bg-[#D9CCF5] border border-black/10 px-4 py-2 text-xs font-bold text-[#1A1A1A] transition-all hover:scale-105 active:scale-95 shadow-xs"
            >
              <svg className="w-3.5 h-3.5 text-[#1A1A1A]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="5 3 19 12 5 21 5 3"></polygon>
              </svg>
              <span>Launch Studio</span>
            </button>
          </div>
        </div>
      </header>
    </div>
  );
};
