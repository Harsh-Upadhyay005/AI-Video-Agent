/**
 * ProtectedRoute component for Video Studio.
 * Requires the user to be authenticated via Clerk before accessing the studio.
 * If not authenticated, renders the themed AuthPage.
 */

import React from 'react';
import { useUser } from '@clerk/react';
import { AuthPage } from './AuthPage';
import { isClerkConfigured } from '../lib/clerk';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  onBackToHome?: () => void;
}

const ClerkProtectedContent: React.FC<ProtectedRouteProps> = ({ children, onBackToHome }) => {
  const { isSignedIn, isLoaded } = useUser();

  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-[#FDFCF0] flex flex-col items-center justify-center pt-20">
        <div className="flex items-center gap-3 px-6 py-4 rounded-2xl bg-white border-2 border-[#1A1A1A] shadow-md">
          <Loader2 className="w-5 h-5 animate-spin text-[#1A1A1A]" />
          <span className="font-['Outfit',sans-serif] font-medium text-sm text-[#1A1A1A]">
            Verifying authentication...
          </span>
        </div>
      </div>
    );
  }

  if (!isSignedIn) {
    return <AuthPage onBack={onBackToHome} />;
  }

  return <>{children}</>;
};

export const ProtectedRoute: React.FC<ProtectedRouteProps> = (props) => {
  if (!isClerkConfigured) {
    return <AuthPage onBack={props.onBackToHome} />;
  }

  return <ClerkProtectedContent {...props} />;
};
