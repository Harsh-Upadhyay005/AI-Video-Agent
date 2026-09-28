/**
 * Supabase client for auth. Missing env vars disable auth instead of crashing the app.
 */

import { createClient, type SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

export const isAuthConfigured = Boolean(supabaseUrl && supabaseAnonKey);

export const supabase: SupabaseClient | null = isAuthConfigured
  ? createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
        storage: window.localStorage,
        storageKey: 'ai-video-agent-auth',
      },
    })
  : null;

export const getCurrentSession = async () => {
  if (!supabase) return null;
  const { data: { session }, error } = await supabase.auth.getSession();
  if (error) {
    console.error('Error getting session:', error);
    return null;
  }
  return session;
};

export const getCurrentUser = async () => {
  if (!supabase) return null;
  const { data: { user }, error } = await supabase.auth.getUser();
  if (error) {
    console.error('Error getting user:', error);
    return null;
  }
  return user;
};

export const getAuthToken = async (): Promise<string | null> => {
  const session = await getCurrentSession();
  return session?.access_token || null;
};
