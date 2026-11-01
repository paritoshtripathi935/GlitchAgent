import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ClerkProvider } from '@clerk/clerk-react';
import './index.css';
import App from './App';
import LandingPage from './pages/LandingPage';

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {PUBLISHABLE_KEY ? (
      <ClerkProvider
        publishableKey={PUBLISHABLE_KEY}
        appearance={{
          variables: {
            colorPrimary: '#3ddc84',
            colorTextOnPrimaryBackground: '#04130a',
            colorBackground: '#0e1013',
            colorInputBackground: '#14171c',
            colorInputText: '#eef1f4',
            colorText: '#eef1f4',
            colorTextSecondary: '#a3acb7',
            colorNeutral: '#ffffff',
            borderRadius: '0.5rem',
            fontFamily: "'Inter', system-ui, sans-serif",
          },
        }}
      >
        <App />
      </ClerkProvider>
    ) : (
      // No Clerk key on this deploy: show the marketing page; CTAs link to the repo.
      <LandingPage />
    )}
  </StrictMode>,
);
