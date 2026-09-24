/**
 * Authentication context — email/password, password reset, profile.
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import { isAuthConfigured, supabase } from '../lib/supabase';
import type { User, Session, AuthContextType } from '../types/auth';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

const AUTH_UNAVAILABLE = new Error(
  'Authentication is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env'
);

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }

    const initializeAuth = async () => {
      try {
        const { data: { session: initialSession } } = await supabase.auth.getSession();
        setSession(initialSession);
        setUser(initialSession?.user ?? null);
      } catch (error) {
        console.error('Error initializing auth:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, nextSession) => {
        setSession(nextSession);
        setUser(nextSession?.user ?? null);
        setLoading(false);
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const signUp = async (email: string, password: string) => {
    if (!supabase) return { error: AUTH_UNAVAILABLE };
    try {
      const { data, error } = await supabase.auth.signUp({ email, password });
      if (error) return { error: new Error(error.message) };
      if (data.user && !data.session) {
        return {
          error: new Error('Please check your email to confirm your account before signing in.'),
        };
      }
      return { error: null };
    } catch (error) {
      return { error: error instanceof Error ? error : new Error('Signup failed') };
    }
  };

  const signIn = async (email: string, password: string) => {
    if (!supabase) return { error: AUTH_UNAVAILABLE };
    try {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) return { error: new Error(error.message) };
      return { error: null };
    } catch (error) {
      return { error: error instanceof Error ? error : new Error('Sign in failed') };
    }
  };

  const signOut = async () => {
    try {
      if (supabase) {
        await supabase.auth.signOut();
      }
      localStorage.removeItem('lastStudioAnalysis');
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  const resetPassword = async (email: string) => {
    if (!supabase) return { error: AUTH_UNAVAILABLE };
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin,
      });
      if (error) return { error: new Error(error.message) };
      return { error: null };
    } catch (error) {
      return { error: error instanceof Error ? error : new Error('Password reset failed') };
    }
  };

  const updatePassword = async (newPassword: string) => {
    if (!supabase) return { error: AUTH_UNAVAILABLE };
    try {
      const { error } = await supabase.auth.updateUser({ password: newPassword });
      if (error) return { error: new Error(error.message) };
      return { error: null };
    } catch (error) {
      return { error: error instanceof Error ? error : new Error('Password update failed') };
    }
  };

  const updateEmail = async (newEmail: string) => {
    if (!supabase) return { error: AUTH_UNAVAILABLE };
    try {
      const { error } = await supabase.auth.updateUser({ email: newEmail });
      if (error) return { error: new Error(error.message) };
      return { error: null };
    } catch (error) {
      return { error: error instanceof Error ? error : new Error('Email update failed') };
    }
  };

  const updateProfile = async (fullName: string) => {
    if (!supabase) return { error: AUTH_UNAVAILABLE };
    try {
      const { error } = await supabase.auth.updateUser({
        data: { full_name: fullName },
      });
      if (error) return { error: new Error(error.message) };
      return { error: null };
    } catch (error) {
      return { error: error instanceof Error ? error : new Error('Profile update failed') };
    }
  };

  const deleteAccount = async () => {
    try {
      await signOut();
      return { error: null };
    } catch (error) {
      return { error: error instanceof Error ? error : new Error('Account deletion failed') };
    }
  };

  const value: AuthContextType = {
    user,
    session,
    loading,
    isAuthConfigured,
    signUp,
    signIn,
    signOut,
    resetPassword,
    updatePassword,
    updateEmail,
    updateProfile,
    deleteAccount,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
