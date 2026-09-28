import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { AppErrorBoundary } from './components/AppErrorBoundary';
import { ClerkProvider } from '@clerk/react';
import { CLERK_PUBLISHABLE_KEY, isClerkConfigured, clerkAppearance } from './lib/clerk';

const root = document.getElementById('root');

if (root) {
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <AppErrorBoundary>
        {isClerkConfigured ? (
          <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY} appearance={clerkAppearance}>
            <App />
          </ClerkProvider>
        ) : (
          <App />
        )}
      </AppErrorBoundary>
    </React.StrictMode>
  );
}
