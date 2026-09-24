/**
 * Completes a password reset after the user follows the email link.
 */

import React, { useState } from 'react';
import { Loader2, Lock, AlertCircle, CheckCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface ResetPasswordFormProps {
  onComplete: () => void;
}

export const ResetPasswordForm: React.FC<ResetPasswordFormProps> = ({ onComplete }) => {
  const { updatePassword } = useAuth();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setLoading(true);
    try {
      const { error: updateError } = await updatePassword(password);
      if (updateError) {
        setError(updateError.message);
      } else {
        setSuccess('Password updated. You can continue to the studio.');
        setTimeout(onComplete, 1200);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pt-28 px-4 min-h-screen bg-[#FDFCF0] flex items-center justify-center">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md bg-white rounded-3xl border-2 border-[#1A1A1A] p-8 space-y-5"
      >
        <h1 className="font-['Baskervville',serif] text-2xl text-[#1A1A1A]">Set a new password</h1>
        {error && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 flex gap-2 text-sm text-red-800">
            <AlertCircle className="w-5 h-5 shrink-0" />
            {error}
          </div>
        )}
        {success && (
          <div className="p-4 rounded-xl bg-green-50 border border-green-200 flex gap-2 text-sm text-green-800">
            <CheckCircle className="w-5 h-5 shrink-0" />
            {success}
          </div>
        )}
        <div className="relative">
          <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8A8A8A]" />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="New password"
            minLength={6}
            className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-[#1A1A1A]/15"
          />
        </div>
        <input
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="Confirm new password"
          minLength={6}
          className="w-full px-4 py-3 rounded-xl border-2 border-[#1A1A1A]/15"
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-xl bg-[#1A1A1A] text-white font-semibold disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Update password'}
        </button>
      </form>
    </div>
  );
};
