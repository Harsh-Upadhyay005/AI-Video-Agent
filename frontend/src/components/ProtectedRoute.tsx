/**
 * Pass-through wrapper kept so the studio layout does not change.
 * Login is not required.
 */

import React from 'react';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  return <>{children}</>;
};
