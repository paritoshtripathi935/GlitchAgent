/**
 * App — auth gate. Signed-out visitors get the landing page (and the Clerk
 * sign-in on demand); signed-in users get the lazy-loaded console.
 */
import { lazy, Suspense, useState } from 'react';
import { useAuth } from '@clerk/clerk-react';
import LandingPage from './pages/LandingPage';
import LoginPage from './components/LoginPage';
import { useTheme } from './hooks/useTheme';

const AuthedApp = lazy(() => import('./AuthedApp'));

// Clerk's `__client_uat` cookie is 0/absent when signed out — render the
// landing page immediately instead of waiting for Clerk to load.
function likelySignedOut() {
  const uats = [...document.cookie.matchAll(/(?:^|; )__client_uat(?:_[^=]*)?=([^;]*)/g)];
  return uats.every(m => !m[1] || m[1] === '0');
}

const Loading = () => (
  <div role="status" className="min-h-screen grid place-items-center text-sm text-dim">Loading GlitchAgent…</div>
);

export default function App() {
  useTheme();
  const { isLoaded, isSignedIn } = useAuth();
  const [signingIn, setSigningIn] = useState(false);
  if (isSignedIn) return <Suspense fallback={<Loading />}><AuthedApp /></Suspense>;
  if (signingIn) return <LoginPage onBack={() => setSigningIn(false)} />;
  if (isLoaded || likelySignedOut()) return <LandingPage onStart={() => setSigningIn(true)} />;
  return <Loading />;
}
