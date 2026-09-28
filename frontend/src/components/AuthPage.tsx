/**
 * Full-page Clerk authentication — sign in and sign up.
 * Matches the project theme: cream background (#FDFCF0), lavender accents (#D9CCF5), Baskervville headings.
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
    <div className="min-h-screen bg-[#FDFCF0] text-[#1A1A1A] pt-24 pb-12 px-4 flex items-center justify-center">
      <div className="mx-auto max-w-5xl w-full grid lg:grid-cols-2 gap-8 items-stretch">
        {/* ── Decorative Left Hero Panel ───────────────────────────── */}
        <div className="hidden lg:flex flex-col justify-between rounded-3xl border-2 border-[#1A1A1A] bg-[#D9CCF5] p-10 min-h-[580px] shadow-sm">
          <div>
            {/* Animated soundwave bars logo */}
            <div className="flex items-end gap-1 h-6 w-8 mb-6">
              <span className="w-1.5 bg-[#1A1A1A] rounded-full soundwave-bar" style={{ animationDelay: '0.1s', height: '100%' }} />
              <span className="w-1.5 bg-[#1A1A1A] rounded-full soundwave-bar" style={{ animationDelay: '0.3s', height: '60%' }} />
              <span className="w-1.5 bg-[#1A1A1A] rounded-full soundwave-bar" style={{ animationDelay: '0.2s', height: '85%' }} />
              <span className="w-1.5 bg-[#1A1A1A] rounded-full soundwave-bar" style={{ animationDelay: '0.4s', height: '50%' }} />
            </div>

            <p className="text-xs font-bold uppercase tracking-widest text-[#1A1A1A]/70 mb-3">
              Flow • Video Studio
            </p>
            <h1 className="font-['Baskervville',serif] text-5xl leading-tight text-[#1A1A1A]">
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
        <div className="bg-white rounded-3xl border-2 border-[#1A1A1A] shadow-xl p-8 sm:p-10 flex flex-col justify-between min-h-[580px]">
          <div>
            {onBack && (
              <button
                type="button"
                onClick={onBack}
                className="mb-6 inline-flex items-center gap-2 text-xs font-bold tracking-wide text-[#8A8A8A] hover:text-[#1A1A1A] transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to overview
              </button>
            )}

            {isClerkConfigured ? (
              <>
                {/* Mode toggle */}
                <div className="flex justify-center mb-6">
                  <div className="flex items-center gap-1 bg-[#F4F3E8] p-1.5 rounded-full border border-black/10">
                    <button
                      onClick={() => setMode('login')}
                      className={`px-5 py-2 rounded-full text-xs font-semibold tracking-wide transition-all ${
                        mode === 'login'
                          ? 'bg-white text-[#1A1A1A] shadow-xs'
                          : 'text-[#8A8A8A] hover:text-[#1A1A1A]'
                      }`}
                    >
                      Sign In
                    </button>
                    <button
                      onClick={() => setMode('signup')}
                      className={`px-5 py-2 rounded-full text-xs font-semibold tracking-wide transition-all ${
                        mode === 'signup'
                          ? 'bg-white text-[#1A1A1A] shadow-xs'
                          : 'text-[#8A8A8A] hover:text-[#1A1A1A]'
                      }`}
                    >
                      Sign Up
                    </button>
                  </div>
                </div>

                {/* Clerk Embed */}
                <div className="flex justify-center w-full">
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
              <div className="space-y-6 animate-fade-in py-2">
                <div className="w-12 h-12 rounded-2xl bg-[#E5D7FA] flex items-center justify-center border border-[#1A1A1A]/10">
                  <KeyRound className="w-6 h-6 text-[#1A1A1A]" />
                </div>

                <div>
                  <h2 className="font-['Baskervville',serif] text-3xl text-[#1A1A1A]">
                    Clerk Authentication Setup
                  </h2>
                  <p className="mt-2 text-sm text-[#8A8A8A] leading-relaxed">
                    Authentication is required to access Video Studio. To connect Clerk, add your Publishable Key to your environment file.
                  </p>
                </div>

                <div className="space-y-3 bg-[#FDFCF0] rounded-2xl p-5 border-2 border-[#1A1A1A]/10">
                  <p className="text-xs font-bold uppercase tracking-wider text-[#1A1A1A]">
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
                    <li>Copy your <strong>Publishable key</strong> (starts with <code className="bg-white px-1.5 py-0.5 rounded border border-black/10">pk_test_</code>)</li>
                    <li>Add it to <code className="bg-white px-1.5 py-0.5 rounded border border-black/10">frontend/.env</code></li>
                  </ol>

                  <div className="mt-4 pt-3 border-t border-[#1A1A1A]/10">
                    <p className="text-[11px] text-[#8A8A8A] mb-1.5 font-semibold">Environment variable format:</p>
                    <div className="flex items-center justify-between bg-white px-3.5 py-2.5 rounded-xl border border-black/15 font-mono text-xs text-[#1A1A1A]">
                      <span className="truncate">{envSnippet}</span>
                      <button
                        type="button"
                        onClick={handleCopy}
                        className="ml-2 p-1.5 rounded-lg hover:bg-[#F4F3E8] transition-colors shrink-0 text-[#1A1A1A]"
                        title="Copy variable"
                      >
                        {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                </div>

                <p className="text-xs text-[#8A8A8A]">
                  After saving <code className="text-[#1A1A1A] font-mono">frontend/.env</code>, restart the frontend dev server to apply changes.
                </p>
              </div>
            )}
          </div>

          <div className="pt-6 border-t border-[#1A1A1A]/10 text-center">
            <p className="text-xs text-[#8A8A8A]">
              By proceeding, you agree to our Terms of Service & Privacy Policy.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
