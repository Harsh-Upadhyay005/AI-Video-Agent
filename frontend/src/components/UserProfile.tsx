/**
 * User Profile Management Component
 * Allows users to manage their account settings and export data
 */

import React, { useState } from 'react';
import { X, User, Mail, Lock, Download, Loader2, AlertCircle, CheckCircle, Trash2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../api/client';

interface UserProfileProps {
  isOpen: boolean;
  onClose: () => void;
}

export const UserProfile: React.FC<UserProfileProps> = ({ isOpen, onClose }) => {
  const { user, updatePassword, updateEmail, updateProfile, deleteAccount } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'data'>('profile');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form states
  const [newEmail, setNewEmail] = useState('');
  const [fullName, setFullName] = useState(
    (user?.user_metadata?.full_name as string) || ''
  );
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [deleteConfirmation, setDeleteConfirmation] = useState('');

  if (!isOpen || !user) return null;

  const handleUpdateEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      const { error } = await updateEmail(newEmail);
      if (error) {
        setError(error.message);
      } else {
        setSuccess('Email update requested! Check your new email to confirm.');
        setNewEmail('');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update email');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setLoading(true);

    try {
      const { error } = await updatePassword(newPassword);
      if (error) {
        setError(error.message);
      } else {
        setSuccess('Password updated successfully!');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update password');
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = async () => {
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      const data = await apiClient.exportUserData();
      
      // Create download link
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ai-video-agent-data-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setSuccess('Data exported successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export data');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== 'DELETE') {
      setError('Please type DELETE to confirm account deletion');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const { error } = await deleteAccount();
      if (error) {
        setError(error.message);
      } else {
        setSuccess('Account deleted successfully. Goodbye!');
        setTimeout(() => {
          onClose();
        }, 2000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete account');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-2xl bg-[#FDFCF0] rounded-3xl border-2 border-[#1A1A1A] shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-[#1A1A1A]/10 shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-[#D9CCF5] flex items-center justify-center">
                <User className="w-6 h-6 text-[#1A1A1A]" />
              </div>
              <div>
                <h2 className="font-['Baskervville',serif] text-2xl text-[#1A1A1A]">
                  Account Settings
                </h2>
                <p className="text-xs text-[#8A8A8A]">{user.email}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              disabled={loading}
              className="w-10 h-10 rounded-full bg-[#1A1A1A]/10 hover:bg-[#1A1A1A]/20 flex items-center justify-center transition-colors disabled:opacity-50"
            >
              <X className="w-5 h-5 text-[#1A1A1A]" />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mt-4">
            <button
              onClick={() => setActiveTab('profile')}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'profile'
                  ? 'bg-[#1A1A1A] text-white'
                  : 'bg-white text-[#8A8A8A] hover:text-[#1A1A1A]'
              }`}
            >
              Profile
            </button>
            <button
              onClick={() => setActiveTab('security')}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'security'
                  ? 'bg-[#1A1A1A] text-white'
                  : 'bg-white text-[#8A8A8A] hover:text-[#1A1A1A]'
              }`}
            >
              Security
            </button>
            <button
              onClick={() => setActiveTab('data')}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'data'
                  ? 'bg-[#1A1A1A] text-white'
                  : 'bg-white text-[#8A8A8A] hover:text-[#1A1A1A]'
              }`}
            >
              Data & Privacy
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Messages */}
          {error && (
            <div className="p-4 rounded-xl bg-red-50 border border-red-200 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-red-900">Error</p>
                <p className="text-xs text-red-700 mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {success && (
            <div className="p-4 rounded-xl bg-green-50 border border-green-200 flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-green-900">Success</p>
                <p className="text-xs text-green-700 mt-0.5">{success}</p>
              </div>
            </div>
          )}

          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div className="space-y-6">
              <div className="bg-white rounded-2xl border border-[#1A1A1A]/10 p-6">
                <h3 className="text-lg font-semibold text-[#1A1A1A] mb-4">Display name</h3>
                <form
                  onSubmit={async (e) => {
                    e.preventDefault();
                    setError(null);
                    setSuccess(null);
                    setLoading(true);
                    try {
                      const { error: profileError } = await updateProfile(fullName.trim());
                      if (profileError) setError(profileError.message);
                      else setSuccess('Profile updated.');
                    } catch (err) {
                      setError(err instanceof Error ? err.message : 'Failed to update profile');
                    } finally {
                      setLoading(false);
                    }
                  }}
                  className="space-y-4"
                >
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Your name"
                    disabled={loading}
                    className="w-full px-4 py-3 rounded-xl border-2 border-[#1A1A1A]/15 bg-white"
                  />
                  <button
                    type="submit"
                    disabled={loading || !fullName.trim()}
                    className="w-full px-4 py-3 rounded-xl bg-[#1A1A1A] text-white font-semibold disabled:opacity-50"
                  >
                    Save name
                  </button>
                </form>
              </div>
              <div className="bg-white rounded-2xl border border-[#1A1A1A]/10 p-6">
                <h3 className="text-lg font-semibold text-[#1A1A1A] mb-4">Email Address</h3>
                <form onSubmit={handleUpdateEmail} className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-[#1A1A1A] mb-2">
                      Current Email
                    </label>
                    <div className="px-4 py-3 rounded-xl border-2 border-[#1A1A1A]/10 bg-[#FDFCF0] text-sm text-[#8A8A8A]">
                      {user.email}
                    </div>
                  </div>
                  <div>
                    <label htmlFor="newEmail" className="block text-sm font-semibold text-[#1A1A1A] mb-2">
                      New Email
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8A8A8A]" />
                      <input
                        id="newEmail"
                        type="email"
                        value={newEmail}
                        onChange={(e) => setNewEmail(e.target.value)}
                        placeholder="new.email@example.com"
                        disabled={loading}
                        className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-[#1A1A1A]/15 bg-white text-[#1A1A1A] placeholder-[#8A8A8A] focus:outline-none focus:ring-2 focus:ring-[#D9CCF5] focus:border-transparent transition-all disabled:opacity-50"
                      />
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={loading || !newEmail}
                    className="w-full px-4 py-3 rounded-xl bg-[#1A1A1A] text-white font-semibold hover:bg-black transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Updating...
                      </>
                    ) : (
                      'Update Email'
                    )}
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              <div className="bg-white rounded-2xl border border-[#1A1A1A]/10 p-6">
                <h3 className="text-lg font-semibold text-[#1A1A1A] mb-4">Change Password</h3>
                <form onSubmit={handleUpdatePassword} className="space-y-4">
                  <div>
                    <label htmlFor="newPassword" className="block text-sm font-semibold text-[#1A1A1A] mb-2">
                      New Password
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8A8A8A]" />
                      <input
                        id="newPassword"
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        placeholder="••••••••"
                        disabled={loading}
                        minLength={6}
                        className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-[#1A1A1A]/15 bg-white text-[#1A1A1A] placeholder-[#8A8A8A] focus:outline-none focus:ring-2 focus:ring-[#D9CCF5] focus:border-transparent transition-all disabled:opacity-50"
                      />
                    </div>
                  </div>
                  <div>
                    <label htmlFor="confirmPassword" className="block text-sm font-semibold text-[#1A1A1A] mb-2">
                      Confirm New Password
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
                        minLength={6}
                        className="w-full pl-11 pr-4 py-3 rounded-xl border-2 border-[#1A1A1A]/15 bg-white text-[#1A1A1A] placeholder-[#8A8A8A] focus:outline-none focus:ring-2 focus:ring-[#D9CCF5] focus:border-transparent transition-all disabled:opacity-50"
                      />
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={loading || !newPassword || !confirmPassword}
                    className="w-full px-4 py-3 rounded-xl bg-[#1A1A1A] text-white font-semibold hover:bg-black transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Updating...
                      </>
                    ) : (
                      'Update Password'
                    )}
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* Data & Privacy Tab */}
          {activeTab === 'data' && (
            <div className="space-y-6">
              {/* Export Data */}
              <div className="bg-white rounded-2xl border border-[#1A1A1A]/10 p-6">
                <h3 className="text-lg font-semibold text-[#1A1A1A] mb-2">Export Your Data</h3>
                <p className="text-sm text-[#8A8A8A] mb-4">
                  Download all your uploaded files, analysis results, and chat history as a JSON file.
                </p>
                <button
                  onClick={handleExportData}
                  disabled={loading}
                  className="w-full px-4 py-3 rounded-xl bg-[#D9CCF5] text-[#1A1A1A] font-semibold hover:bg-[#D9CCF5]/80 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Exporting...
                    </>
                  ) : (
                    <>
                      <Download className="w-5 h-5" />
                      Download My Data
                    </>
                  )}
                </button>
              </div>

              {/* Delete Account */}
              <div className="bg-red-50 rounded-2xl border border-red-200 p-6">
                <h3 className="text-lg font-semibold text-red-900 mb-2 flex items-center gap-2">
                  <Trash2 className="w-5 h-5" />
                  Delete Account
                </h3>
                <p className="text-sm text-red-700 mb-4">
                  This will permanently delete your account and all associated data. This action cannot be undone.
                </p>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-semibold text-red-900 mb-2">
                      Type "DELETE" to confirm
                    </label>
                    <input
                      type="text"
                      value={deleteConfirmation}
                      onChange={(e) => setDeleteConfirmation(e.target.value)}
                      placeholder="DELETE"
                      disabled={loading}
                      className="w-full px-4 py-3 rounded-xl border-2 border-red-300 bg-white text-[#1A1A1A] placeholder-red-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all disabled:opacity-50"
                    />
                  </div>
                  <button
                    onClick={handleDeleteAccount}
                    disabled={loading || deleteConfirmation !== 'DELETE'}
                    className="w-full px-4 py-3 rounded-xl bg-red-600 text-white font-semibold hover:bg-red-700 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Deleting...
                      </>
                    ) : (
                      <>
                        <Trash2 className="w-5 h-5" />
                        Delete My Account
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
