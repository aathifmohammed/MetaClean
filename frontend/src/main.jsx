import React from 'react';
import { createRoot } from 'react-dom/client';
import { GoogleOAuthProvider } from '@react-oauth/google';
import App from './App.jsx';
import './styles.css';

const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

function Root() {
  // The app still works for guest users when Google sign-in is not configured.
  if (!clientId) return <App />;
  return <GoogleOAuthProvider clientId={clientId}><App /></GoogleOAuthProvider>;
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode><Root /></React.StrictMode>,
);
