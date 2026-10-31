import { useState } from 'react';
import { LogOut, Moon, RefreshCw, Sun, UserRound } from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';

export function SignedInHeader({ user, onSignOut }) {
  const [avatarUnavailable, setAvatarUnavailable] = useState(false);
  return <div className="signed-in"><div className="avatar">{user.picture && !avatarUnavailable ? <img src={user.picture} alt="" referrerPolicy="no-referrer" onError={() => setAvatarUnavailable(true)} /> : <UserRound size={18} />}</div><div className="user-summary"><b>{user.name || user.email || 'Signed in'}</b><small>Google account</small></div><button className="icon-button" title="Sign out" onClick={onSignOut}><LogOut size={17} /></button></div>;
}

export function SignedOutHeader({ clientId, onSuccess, onError }) {
  return <div className="login-area">{clientId ? <GoogleLogin onSuccess={onSuccess} onError={onError} size="medium" shape="pill" text="signin_with" /> : <span className="guest-label"><UserRound size={15} /> Guest mode</span>}</div>;
}

export default function HeaderActions({ theme, onToggleTheme, onRefresh, user, onSignOut, clientId, onLoginSuccess, onLoginError }) {
  return <div className="topbar-actions"><button className="icon-button theme-toggle" title={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`} aria-label="Toggle theme" onClick={onToggleTheme}>{theme === 'light' ? <Moon size={17} /> : <Sun size={17} />}</button><button className="icon-button" title="Refresh service status" onClick={onRefresh}><RefreshCw size={17} /></button>{user ? <SignedInHeader user={user} onSignOut={onSignOut} /> : <SignedOutHeader clientId={clientId} onSuccess={onLoginSuccess} onError={onLoginError} />}</div>;
}
