/**
 * Authentication types for Supabase Auth integration
 */

import type { User, Session } from '@supabase/supabase-js';

export type { User, Session };

export interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  isAuthConfigured: boolean;
  signUp: (email: string, password: string) => Promise<{ error: Error | null }>;
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ error: Error | null }>;
  updatePassword: (newPassword: string) => Promise<{ error: Error | null }>;
  updateEmail: (newEmail: string) => Promise<{ error: Error | null }>;
  updateProfile: (fullName: string) => Promise<{ error: Error | null }>;
  deleteAccount: () => Promise<{ error: Error | null }>;
}

export interface AuthError {
  message: string;
  status?: number;
}
