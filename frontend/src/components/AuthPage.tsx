/**
 * Full-page email/password login and signup.
 */

import React, { useState } from 'react';
import { Loader2, Mail, Lock, AlertCircle, CheckCircle, ArrowLeft } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface AuthPageProps {
  defaultMode?: 'login' | 'signup';
  onSuccess?: () => void;
  onBack?: () => void;
}

type AuthMode = 'login' | 'signup';

export const AuthPage: React.FC<AuthPageProps> = ({
  defaultMode = 'login',
  onSuccess,
  onBack,
}) => {
  const { signIn, signUp, resetPassword, isAuthConfigured } = useAuth();
  const [mode, setMode] = useState<AuthMode>(defaultMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showForgotPassword, setShowForgotPassword] = useState(false);

  const resetForm = () => {
    setPassword('');
    setConfirmPassword('');
    setError(null);
    setSuccess(null);
    setShowForgotPassword(false);
  };

  const switchMode = (newMode: AuthMode) => {
    setMode(newMode);
    resetForm();
  };

  const validateEmail = (value: string): boolean => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);

  const handleForgotPassword = async () => {
    if (!validateEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { error: resetError } = await resetPassword(email);
      if (resetError) {
        setError(resetError.message);
      } else {
        setSuccess('Password reset email sent. Check your inbox.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send reset email');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (showForgotPassword) {
      await handleForgotPassword();
      return;
    }

    if (!validateEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }
    if (mode === 'signup' && password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      if (mode === 'signup') {
        const { error: signUpError } = await signUp(email, password);
        if (signUpError) {
          setError(signUpError.message);
        } else {
          setSuccess('Account created. You can now sign in.');
          setTimeout(() => {
            switchMode('login');
            setSuccess(null);
            onSuccess?.();
          }, 1200);
        }
      } else {
        const { error: signInError } = await signIn(email, password);
        if (signInError) {
          setError(signInError.message);
        } else {
          setSuccess('Signed in.');
          setTimeout(() => {
            onSuccess?.();
          }, 400);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const title = showForgotPassword
    ? 'Reset password'
    : mode === 'login'
      ? 'Welcome back'
      : 'Create your account';

  const subtitle = showForgotPassword
    ? 'Enter your email and we will send a reset link.'
    : mode === 'login'
      ? 'Sign in with your email to open Video Studio.'
      : 'Sign up with email. No Google or GitHub required.';

  return (
    <div className="min-h-screen bg-[#FDFCF0] text-[#1A1A1A] pt-24 pb-12 px-4">
      <div className="mx-auto max-w-5xl grid lg:grid-cols-2 gap-8 items-stretch">
        <div className="hidden lg:flex flex-col justify-between rounded-3xl border-2 border-[#1A1A1A] bg-[#D9CCF5] p-10 min-h-[560px]">
          <div>
            <div className="flex items-end gap-0.5 h-5 w-6 mb-6">
              <span className="w-1 bg-[#1A1A1A] rounded-full h-full" />
              <span className="w-1 bg-[#1A1A1A] rounded-full h-3/5" />
              <span className="w-1 bg-[#1A1A1A] rounded-full h-4/5" />
              <span className="w-1 bg-[#1A1A1A] rounded-full h-1/2" />
            </div>
            <p className="text-xs font-bold uppercase tracking-widest text-[#1A1A1A]/60 mb-3">
              Flow
            </p>
            <h1 className="font-['Baskervville',serif] text-5xl leading-tight">
              Analyze video.
              <br />
              Ask anything.
            </h1>
            <p className="mt-6 text-sm leading-relaxed text-[#1A1A1A]/80 max-w-sm">
              Sign in to transcribe YouTube, audio, and PDF files, then chat with the content using RAG.
            </p>
          </div>
          <p className="text-xs text-[#1A1A1A]/50">
            YouTube • MP3/MP4 • PDF • Hinglish
          </p>
        </div>

        <div className="bg-white rounded-3xl border-2 border-[#1A1A1A] shadow-xl p-8 sm:p-10 flex flex-col">
          {onBack && (
            <button
              type="button"
              onClick={onBack}
              disabled={loading}
              className="mb-6 inline-flex items-center gap-2 text-xs font-semibold text-[#8A8A8A] hover:text-[#1A1A1A]"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to overview
            </button>
          )}

          <h2 className="font-['Baskervville',serif] text-3xl mb-2">{title}</h2>
          <p className="text-sm text-[#8A8A8A] mb-8">{subtitle}</p>

          <form onSubmit={handleSubmit} className="space-y-5 flex-1">
            {!isAuthConfigured && (
              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900">
                Auth is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to frontend/.env.
              </div>
            )}

            {error && (
              <div className="p-4 rounded-xl bg-red-50 border border-red-200 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-red-900">Error</p>
                  <p className="text-xs text-red-700 mt-0.5">{error}</p>
                </div>
              </div>
            )}

            {success && (
              <div className="p-4 rounded-xl bg-green-50 border border-green-200 flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-green-900">Success</p>
                  <p className="text-xs text-green-700 mt-0.5">{success}</p>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-semibold">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8A8A8A]" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  disabled={loading}
                  required
                  autoComplete="email"
                  className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-[#1A1A1A]/15 bg-[#FDFCF0] text-[#1A1A1A] placeholder-[#8A8A8A] focus:outline-none focus:ring-2 focus:ring-[#D9CCF5] disabled:opacity-50"
                />
              </div>
            </div>

            {!showForgotPassword && (
              <div className="space-y-2">
                <label htmlFor="password" className="block text-sm font-semibold">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8A8A8A]" />
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    disabled={loading}
                    required
                    minLength={6}
                    autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                    className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-[#1A1A1A]/15 bg-[#FDFCF0] text-[#1A1A1A] placeholder-[#8A8A8A] focus:outline-none focus:ring-2 focus:ring-[#D9CCF5] disabled:opacity-50"
                  />
                </div>
              </div>
            )}

            {!showForgotPassword && mode === 'signup' && (
              <div className="space-y-2">
                <label htmlFor="confirmPassword" className="block text-sm font-semibold">
                  Confirm password
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8A8A8A]" />
                  <input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    disabled={loading}
                    required
                    autoComplete="new-password"
                    className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-[#1A1A1A]/15 bg-[#FDFCF0] text-[#1A1A1A] placeholder-[#8A8A8A] focus:outline-none focus:ring-2 focus:ring-[#D9CCF5] disabled:opacity-50"
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !isAuthConfigured}
              className="w-full px-6 py-4 rounded-xl bg-[#1A1A1A] text-white font-semibold hover:bg-black transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {showForgotPassword ? 'Sending...' : mode === 'login' ? 'Signing in...' : 'Creating account...'}
                </>
              ) : showForgotPassword ? (
                'Send reset link'
              ) : mode === 'login' ? (
                'Sign in'
              ) : (
                'Create account'
              )}
            </button>

            {!showForgotPassword && mode === 'login' && (
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => {
                    setShowForgotPassword(true);
                    setError(null);
                    setSuccess(null);
                  }}
                  disabled={loading}
                  className="text-sm text-[#8A8A8A] hover:text-[#1A1A1A]"
                >
                  Forgot your password?
                </button>
              </div>
            )}

            {showForgotPassword && (
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => setShowForgotPassword(false)}
                  disabled={loading}
                  className="text-sm text-[#8A8A8A] hover:text-[#1A1A1A]"
                >
                  Back to sign in
                </button>
              </div>
            )}

            {!showForgotPassword && (
              <div className="pt-4 border-t border-[#1A1A1A]/10 text-center">
                <p className="text-sm text-[#8A8A8A]">
                  {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}{' '}
                  <button
                    type="button"
                    onClick={() => switchMode(mode === 'login' ? 'signup' : 'login')}
                    disabled={loading}
                    className="font-semibold text-[#1A1A1A]"
                  >
                    {mode === 'login' ? 'Sign up' : 'Sign in'}
                  </button>
                </p>
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};
