/**
 * Clerk configuration and helpers.
 * Missing VITE_CLERK_PUBLISHABLE_KEY disables auth instead of crashing.
 */

export const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || '';

export const isClerkConfigured = Boolean(CLERK_PUBLISHABLE_KEY);

/**
 * Clerk appearance theme that matches the project design system.
 * Cream background (#FDFCF0), lavender accents (#D9CCF5), dark text (#1A1A1A).
 */
export const clerkAppearance = {
  variables: {
    colorPrimary: '#1A1A1A',
    colorBackground: '#FDFCF0',
    colorText: '#1A1A1A',
    colorTextSecondary: '#8A8A8A',
    colorInputBackground: '#FDFCF0',
    colorInputText: '#1A1A1A',
    borderRadius: '0.75rem',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    fontFamilyButtons: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  },
  elements: {
    card: 'shadow-none border-0 bg-transparent',
    rootBox: 'w-full',
    formButtonPrimary:
      'bg-[#1A1A1A] hover:bg-black text-white font-semibold rounded-xl py-3 text-sm transition-all shadow-none',
    formFieldInput:
      'rounded-xl border-2 border-[#1A1A1A]/15 bg-[#FDFCF0] text-[#1A1A1A] placeholder-[#8A8A8A] focus:ring-2 focus:ring-[#D9CCF5] focus:border-transparent py-3',
    formFieldLabel: 'text-sm font-semibold text-[#1A1A1A]',
    headerTitle: "font-['Baskervville',serif] text-3xl text-[#1A1A1A]",
    headerSubtitle: 'text-sm text-[#8A8A8A]',
    socialButtonsBlockButton:
      'rounded-xl border-2 border-[#1A1A1A]/15 bg-white hover:bg-[#F4F3E8] text-[#1A1A1A] font-semibold py-3 transition-all',
    socialButtonsBlockButtonText: 'text-sm font-semibold',
    dividerLine: 'bg-[#1A1A1A]/10',
    dividerText: 'text-xs text-[#8A8A8A]',
    footerActionLink: 'text-[#1A1A1A] font-semibold hover:text-[#1A1A1A]/80',
    identityPreviewEditButton: 'text-[#8A8A8A] hover:text-[#1A1A1A]',
    formFieldErrorText: 'text-red-600 text-xs',
    alertText: 'text-sm',
    userButtonPopoverCard: 'rounded-2xl border-2 border-[#1A1A1A]/10 shadow-xl',
    userButtonPopoverActionButton: 'hover:bg-[#F4F3E8]',
    userButtonAvatarBox: 'w-8 h-8 rounded-full',
  },
};
