/**
 * Full-page Clerk authentication — sign in and sign up.
 * Matches the project theme: cream background (#FDFCF0), lavender accents (#D9CCF5), Baskervville headings.
 * Fully responsive across mobile, tablet, and desktop devices.
 */

import { useState } from 'react';
import type React from 'react';
import { SignIn, SignUp } from '@clerk/react';
import { ArrowLeft, KeyRound, Copy, Check, ExternalLink } from 'lucide-react';
import { clerkAppearance, isClerkConfigured } from '../lib/clerk';

interface AuthPageProps {
  defaultMode?: 'login' | 'signup';
  onBack?: () => void;
}

type AuthMode = 'login' | 'signup';

export const AuthPage: React.FC<AuthPageProps> = ({
  defaultMode = 'login',
  onBack,
}) => {
  const [mode, setMode] = useState<AuthMode>(defaultMode);
  const [copied, setCopied] = useState(false);

  const envSnippet = 'VITE_CLERK_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE';

  const handleCopy = () => {
    navigator.clipboard.writeText(envSnippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-[#FDFCF0] text-[#1A1A1A] pt-20 sm:pt-24 pb-8 sm:pb-12 px-3 sm:px-6 flex items-center justify-center">
      <div className="mx-auto max-w-5xl w-full grid lg:grid-cols-2 gap-6 sm:gap-8 items-stretch">
        {/* ── Decorative Left Hero Panel (Desktop) ────────────────── */}
        <div className="hidden lg:flex flex-col justify-between rounded-3xl border-2 border-[#1A1A1A] bg-[#D9CCF5] p-8 sm:p-10 min-h-[580px] shadow-sm">
          <div>
            {/* Animated soundwave bars logo */}
            <div className="flex items-end gap-1 h-6 w-8 mb-6">
              <span className="w-1.5 bg-[#1A1A1A] rounded-full soundwave-bar" style={{ animationDelay: '0.1s', height: '100%' }} />
              <span className="w-1.5 bg-[#1A1A1A] rounded-full soundwave-bar" style={{ animationDelay: '0.3s', height: '60%' }} />
              <span className="w-1.5 bg-[#1A1A1A] rounded-full soundwave-bar" style={{ animationDelay: '0.2s', height: '85%' }} />
              <span className="w-1.5 bg-[#1A1A1A] rounded-full soundwave-bar" style={{ animationDelay: '0.4s', height: '50%' }} />
            </div>

            <p className="text-xs font-bold uppercase tracking-widest text-[#1A1A1A]/70 mb-3">
              videoQuery • Video Studio
            </p>
            <h1 className="font-['Baskervville',serif] text-4xl sm:text-5xl leading-tight text-[#1A1A1A]">
              Analyze video.
              <br />
              Ask anything.
            </h1>
            <p className="mt-6 text-sm leading-relaxed text-[#1A1A1A]/85 max-w-sm">
              Sign in to unlock AI Video Studio. Transcribe YouTube, MP3/MP4, and PDF documents, then converse with the content using RAG.
            </p>
          </div>

          {/* Feature Badges */}
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {['🎬 YouTube Transcribe', '🎙️ Local Whisper', '📄 PDF RAG', '⚡ Sarvam AI'].map((tag) => (
                <span
                  key={tag}
                  className="px-3.5 py-1.5 rounded-full bg-white/80 border border-[#1A1A1A]/10 text-xs font-semibold text-[#1A1A1A]"
                >
                  {tag}
                </span>
              ))}
            </div>
            <p className="text-xs text-[#1A1A1A]/60">
              Secured by Clerk Authentication
            </p>
          </div>
        </div>

        {/* ── Right Auth Panel ────────────────────────────────────── */}
        <div className="bg-white rounded-3xl border-2 border-[#1A1A1A] shadow-xl p-4 sm:p-8 md:p-10 flex flex-col justify-between min-h-[520px] sm:min-h-[580px] w-full">
          <div>
            {/* Top Row: Back button & Mobile Brand */}
            <div className="flex items-center justify-between mb-4 sm:mb-6">
              {onBack ? (
                <button
                  type="button"
                  onClick={onBack}
                  className="inline-flex items-center gap-1.5 sm:gap-2 text-xs font-bold tracking-wide text-[#8A8A8A] hover:text-[#1A1A1A] transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back to overview</span>
                </button>
              ) : <div />}

              {/* Mobile-only brand tag */}
              <div className="lg:hidden flex items-center gap-1.5">
                <div className="flex items-end gap-0.5 h-3.5 w-4">
                  <span className="w-0.75 bg-[#1A1A1A] rounded-full soundwave-bar" style={{ animationDelay: '0.1s', height: '100%' }} />
                  <span className="w-0.75 bg-[#1A1A1A] rounded-full soundwave-bar" style={{ animationDelay: '0.3s', height: '60%' }} />
                  <span className="w-0.75 bg-[#1A1A1A] rounded-full soundwave-bar" style={{ animationDelay: '0.2s', height: '80%' }} />
                </div>
                <span className="font-['Outfit',sans-serif] font-bold text-sm text-[#1A1A1A]">videoQuery</span>
              </div>
            </div>

            {/* Mobile Title Banner */}
            <div className="lg:hidden text-center mb-6">
              <h2 className="font-['Baskervville',serif] text-2xl sm:text-3xl text-[#1A1A1A]">
                Sign in to Video Studio
              </h2>
              <p className="text-xs text-[#8A8A8A] mt-1">
                Access AI video & PDF analyzers with RAG chat
              </p>
            </div>

            {isClerkConfigured ? (
              <>
                {/* Mode toggle */}
                <div className="flex justify-center mb-4 sm:mb-6">
                  <div className="flex items-center gap-1 bg-[#F4F3E8] p-1 rounded-full border border-black/10">
                    <button
                      onClick={() => setMode('login')}
                      className={`px-4 sm:px-5 py-1.5 sm:py-2 rounded-full text-xs font-semibold tracking-wide transition-all ${
                        mode === 'login'
                          ? 'bg-white text-[#1A1A1A] shadow-xs'
                          : 'text-[#8A8A8A] hover:text-[#1A1A1A]'
                      }`}
                    >
                      Sign In
                    </button>
                    <button
                      onClick={() => setMode('signup')}
                      className={`px-4 sm:px-5 py-1.5 sm:py-2 rounded-full text-xs font-semibold tracking-wide transition-all ${
                        mode === 'signup'
                          ? 'bg-white text-[#1A1A1A] shadow-xs'
                          : 'text-[#8A8A8A] hover:text-[#1A1A1A]'
                      }`}
                    >
                      Sign Up
                    </button>
                  </div>
                </div>

                {/* Clerk Component Form */}
                <div className="flex justify-center w-full overflow-x-auto">
                  {mode === 'login' ? (
                    <SignIn
                      appearance={clerkAppearance}
                      routing="hash"
                      signUpUrl="#signup"
                    />
                  ) : (
                    <SignUp
                      appearance={clerkAppearance}
                      routing="hash"
                      signInUrl="#login"
                    />
                  )}
                </div>
              </>
            ) : (
              /* Setup Instructions when Clerk publishable key is not set */
              <div className="space-y-4 sm:space-y-6 animate-fade-in py-2">
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-2xl bg-[#E5D7FA] flex items-center justify-center border border-[#1A1A1A]/10">
                  <KeyRound className="w-5 h-5 sm:w-6 sm:h-6 text-[#1A1A1A]" />
                </div>

                <div>
                  <h2 className="font-['Baskervville',serif] text-2xl sm:text-3xl text-[#1A1A1A]">
                    Clerk Authentication Setup
                  </h2>
                  <p className="mt-1 sm:mt-2 text-xs sm:text-sm text-[#8A8A8A] leading-relaxed">
                    Authentication is required to access Video Studio. To connect Clerk, add your Publishable Key to your environment file.
                  </p>
                </div>

                <div className="space-y-3 bg-[#FDFCF0] rounded-2xl p-4 sm:p-5 border-2 border-[#1A1A1A]/10">
                  <p className="text-[11px] sm:text-xs font-bold uppercase tracking-wider text-[#1A1A1A]">
                    Quick Setup Steps:
                  </p>
                  <ol className="text-xs text-[#1A1A1A]/80 space-y-2 list-decimal list-inside leading-relaxed font-medium">
                    <li>
                      Create a free app at{' '}
                      <a
                        href="https://dashboard.clerk.com"
                        target="_blank"
                        rel="noreferrer"
                        className="text-[#1A1A1A] underline font-bold inline-flex items-center gap-1"
                      >
                        dashboard.clerk.com <ExternalLink className="w-3 h-3" />
                      </a>
                    </li>
                    <li>Go to <strong>API Keys</strong> in your Clerk Dashboard</li>
                    <li>Copy your <strong>Publishable key</strong> (starts with <code className="bg-white px-1 py-0.5 rounded border border-black/10">pk_test_</code>)</li>
                    <li>Add it to <code className="bg-white px-1 py-0.5 rounded border border-black/10">frontend/.env</code></li>
                  </ol>

                  <div className="mt-4 pt-3 border-t border-[#1A1A1A]/10">
                    <p className="text-[10px] sm:text-[11px] text-[#8A8A8A] mb-1 font-semibold">Environment variable format:</p>
                    <div className="flex items-center justify-between bg-white px-2.5 sm:px-3.5 py-2 sm:py-2.5 rounded-xl border border-black/15 font-mono text-[11px] sm:text-xs text-[#1A1A1A] gap-2">
                      <span className="truncate">{envSnippet}</span>
                      <button
                        type="button"
                        onClick={handleCopy}
                        className="p-1 sm:p-1.5 rounded-lg hover:bg-[#F4F3E8] transition-colors shrink-0 text-[#1A1A1A]"
                        title="Copy variable"
                      >
                        {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                </div>

                <p className="text-[11px] sm:text-xs text-[#8A8A8A]">
                  After saving <code className="text-[#1A1A1A] font-mono">frontend/.env</code>, restart the frontend dev server to apply changes.
                </p>
              </div>
            )}
          </div>

          <div className="pt-4 sm:pt-6 border-t border-[#1A1A1A]/10 text-center mt-6">
            <p className="text-[10px] sm:text-xs text-[#8A8A8A]">
              By proceeding, you agree to our Terms of Service & Privacy Policy.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
