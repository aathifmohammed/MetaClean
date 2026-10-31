import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity, AlertCircle, ArrowDownToLine, ArrowRight, Check, CheckCircle2,
  CircleHelp, Clock3, CloudUpload, Code2, Copy, Database,
  FileImage, FileSearch, Image as ImageIcon, LoaderCircle,
  LogIn, LogOut, Moon, RefreshCw, Search, Sparkles, Sun, Trash2, Upload,
  UserRound, X, Zap,
} from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';
import { apiDownload, apiRequest, apiUrl, downloadBlob, formatDate } from './api';
import metaCleanLogoDark from '../assets/Glossy MetaClean Shield Logo Transparent.png';
import metaCleanLogoLight from '../assets/Glossy MetaClean Shield Logo Light.png';
import { PageHeading, SignInCard, ImageWorkspace, MetadataResults, Metric, EmptyState, EndpointCard } from './components/WorkspaceComponents';
import MainNavigation from './components/navigation/MainNavigation';
import HeaderActions from './components/layout/HeaderActions';
import CheckMetadataScreen from './components/screens/CheckMetadataScreen';
import CleanMetadataScreen from './components/screens/CleanMetadataScreen';
import EndpointsScreen from './components/screens/EndpointsScreen';
import ActivityScreen from './components/screens/ActivityScreen';
import PublicEndpointScreen from './components/screens/PublicEndpointScreen';


function App() {
  const [activeTab, setActiveTab] = useState('check');
  const [token, setToken] = useState(() => Number(localStorage.getItem('metaclean_session_expires') || 0) > Date.now() ? 'cookie-session' : '');
  const [user, setUser] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking');
  const [databaseStatus, setDatabaseStatus] = useState('checking');
  const [toast, setToast] = useState('');
  const [busy, setBusy] = useState(false);
  const [cleaningMode, setCleaningMode] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [checkResult, setCheckResult] = useState(null);
  const [lastClean, setLastClean] = useState(null);
  const [activities, setActivities] = useState([]);
  const [endpoints, setEndpoints] = useState([]);
  const [newEndpointName, setNewEndpointName] = useState('');
  const [editingId, setEditingId] = useState('');
  const [editingName, setEditingName] = useState('');
  const [endpointFiles, setEndpointFiles] = useState({});
  const [endpointModes, setEndpointModes] = useState({});
  const [uploadingEndpoint, setUploadingEndpoint] = useState('');
  const [publicId, setPublicId] = useState('');
  const [publicData, setPublicData] = useState(null);
  const [publicLoading, setPublicLoading] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('metaclean_theme') || 'light');
  useEffect(() => { document.documentElement.dataset.theme = theme; localStorage.setItem('metaclean_theme', theme); }, [theme]);

  const showToast = useCallback((message) => {
    setToast(message);
    window.setTimeout(() => setToast(''), 4500);
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      await apiRequest('/health');
      setBackendStatus('online');
    } catch {
      setBackendStatus('offline');
    }
    try {
      const result = await apiRequest('/health/database');
      setDatabaseStatus(result?.database === 'connected' ? 'connected' : 'offline');
    } catch {
      setDatabaseStatus('offline');
    }
  }, []);

  const refreshAccountData = useCallback(async (activeToken = token) => {
    if (!activeToken) {
      setUser(null); setActivities([]); setEndpoints([]);
      return;
    }
    try {
      const [profile, activityRows, endpointRows] = await Promise.all([
        apiRequest('/api/account/me', {}, activeToken),
        apiRequest('/api/account/activities', {}, activeToken),
        apiRequest('/api/endpoints', {}, activeToken),
      ]);
      setUser(profile);
      setActivities(Array.isArray(activityRows) ? activityRows : []);
      setEndpoints(Array.isArray(endpointRows) ? endpointRows : []);
    } catch (error) {
      const credentialRejected = /401|invalid or expired|sign in with google/i.test(error.message);
      if (credentialRejected) {
        localStorage.removeItem('metaclean_session_expires');
        setToken(''); setUser(null); setActivities([]); setEndpoints([]);
      }
      showToast(credentialRejected
        ? error.message
        : /database is currently unavailable|database/i.test(error.message)
        ? 'Google sign-in succeeded, but MetaClean account data is unavailable because the database cannot be reached.'
        : `Account data could not be loaded: ${error.message}`);
    }
  }, [token, showToast]);

  useEffect(() => { checkHealth(); }, [checkHealth]);
  useEffect(() => { if (token) refreshAccountData(token); }, [token, refreshAccountData]);
  useEffect(() => {
    if (!selectedFile) { setPreviewUrl(''); return; }
    const url = URL.createObjectURL(selectedFile);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [selectedFile]);

  const onLoginSuccess = async (credentialResponse) => {
    if (!credentialResponse?.credential) {
      showToast('Google did not return an ID token. Please try again.');
      return;
    }
    setUser(readGoogleProfile(credentialResponse.credential));
    try {
      const profile = await apiRequest('/api/account/session', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ credential: credentialResponse.credential }) });
      localStorage.setItem('metaclean_session_expires', String(Date.now() + 7 * 24 * 60 * 60 * 1000));
      setToken('cookie-session'); setUser(profile);
      showToast('Signed in. You will stay signed in for 7 days on this browser.');
    } catch (error) {
      setUser(null);
      showToast(`Could not create your MetaClean session: ${error.message}`);
    }
  };

  const signOut = () => {
    apiRequest('/api/account/session/logout', { method: 'POST' }).catch(() => {});
    localStorage.removeItem('metaclean_session_expires');
    setToken(''); setUser(null); setActivities([]); setEndpoints([]);
    showToast('Signed out from MetaClean.');
  };

  const chooseFile = (file, autoCheck = false) => {
    if (!file) return;
    setSelectedFile(file);
    setCheckResult(null);
    setLastClean(null);
    if (autoCheck) checkMetadata(file, false);
  };

  const removeSelectedFile = () => { setSelectedFile(null); setCheckResult(null); setLastClean(null); };

  const checkMetadata = async (fileToInspect = selectedFile, recordActivity = true) => {
    const targetFile = fileToInspect || selectedFile;
    if (!targetFile) return showToast('Choose an image first.');
    const form = new FormData(); form.append('file', targetFile);
    form.append('record_activity', String(recordActivity));
    setBusy(true); setCheckResult(null);
    try {
      const result = await apiRequest('/api/metadata/check', { method: 'POST', body: form }, token || null);
      setCheckResult(result);
      if (token) refreshAccountData(token);
    } catch (error) { showToast(`Could not check image: ${error.message}`); }
    finally { setBusy(false); }
  };

  const cleanMetadata = async (modeOverride = 'all') => {
    if (!selectedFile) return showToast('Choose an image first.');
    const mode = modeOverride;
    const form = new FormData(); form.append('file', selectedFile); form.append('mode', mode);
    setCleaningMode(mode);
    try {
      const result = await apiDownload('/api/metadata/clean', form, token || null);
      downloadBlob(result.blob, result.filename);
      setLastClean({
        filename: result.filename,
        mode: mode,
        size: result.blob.size,
        blob: result.blob,
      });
      if (token) await refreshAccountData(token);
      showToast(`Cleaned image (${mode === 'ai_only' ? 'AI metadata only' : 'All metadata'}) downloaded successfully.`);
    } catch (error) { showToast(`Could not clean image: ${error.message}`); }
    finally { setCleaningMode(''); }
  };

  const loadSampleImage = async (type, autoCheck = false) => {
    setBusy(true);
    try {
      const response = await fetch(apiUrl(`/api/metadata/samples/${type}`));
      if (!response.ok) throw new Error('Failed to load sample image');
      const blob = await response.blob();
      const filename = type === 'ai' ? 'sample-ai-midjourney.jpg' : 'sample-camera-photo.jpg';
      const file = new File([blob], filename, { type: 'image/jpeg' });
      chooseFile(file, autoCheck);
      showToast(type === 'ai' ? 'Loaded sample AI image with Midjourney & SDXL markers!' : 'Loaded sample camera photo with Canon EXIF!');
    } catch (err) {
      showToast(`Sample error: ${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const verifyCleanedFile = async () => {
    if (!lastClean?.blob) return;
    const file = new File([lastClean.blob], lastClean.filename, { type: 'image/jpeg' });
    setActiveTab('check');
    setSelectedFile(file);
    await checkMetadata(file);
    showToast('Verified cleaned image! Notice 0 AI markers remain.');
  };

  const createEndpoint = async (event) => {
    event.preventDefault();
    const name = newEndpointName.trim();
    if (!name) return;
    try {
      await apiRequest('/api/endpoints', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) }, token);
      setNewEndpointName(''); await refreshAccountData(token); showToast('Endpoint created.');
    } catch (error) { showToast(`Could not create endpoint: ${error.message}`); }
  };

  const saveEndpointName = async (endpointId) => {
    const name = editingName.trim();
    if (!name) return showToast('Endpoint name cannot be empty.');
    try {
      await apiRequest(`/api/endpoints/${encodeURIComponent(endpointId)}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) }, token);
      setEditingId(''); setEditingName(''); await refreshAccountData(token); showToast('Endpoint renamed.');
    } catch (error) { showToast(`Could not rename endpoint: ${error.message}`); }
  };

  const deleteEndpoint = async (endpoint) => {
    if (!window.confirm(`Delete “${endpoint.name}” and its stored images? This cannot be undone.`)) return;
    try {
      await apiRequest(`/api/endpoints/${encodeURIComponent(endpoint.endpoint_id)}`, { method: 'DELETE' }, token);
      await refreshAccountData(token); showToast('Endpoint deleted.');
    } catch (error) { showToast(`Could not delete endpoint: ${error.message}`); }
  };

  const uploadEndpointImage = async (endpoint) => {
    const file = endpointFiles[endpoint.endpoint_id];
    if (!file) return showToast('Choose an image to save to this endpoint.');
    const form = new FormData(); form.append('file', file); form.append('mode', endpointModes[endpoint.endpoint_id] || 'all');
    setUploadingEndpoint(endpoint.endpoint_id);
    try {
      await apiRequest(`/api/endpoints/${encodeURIComponent(endpoint.endpoint_id)}/images`, { method: 'POST', body: form }, token);
      setEndpointFiles((old) => ({ ...old, [endpoint.endpoint_id]: null }));
      await refreshAccountData(token); showToast('Cleaned image saved to endpoint. The endpoint retains up to 10 images.');
    } catch (error) { showToast(`Image upload failed: ${error.message}`); }
    finally { setUploadingEndpoint(''); }
  };

  const deleteEndpointImage = async (endpointId, imageId) => {
    if (!window.confirm('Delete this stored image?')) return;
    try {
      await apiRequest(`/api/endpoints/${encodeURIComponent(endpointId)}/images/${encodeURIComponent(imageId)}`, { method: 'DELETE' }, token);
      showToast('Image deleted.');
      if (publicId === endpointId) loadPublicEndpoint(endpointId);
      await refreshAccountData(token);
    } catch (error) { showToast(`Could not delete image: ${error.message}`); }
  };

  const loadPublicEndpoint = async (id = publicId) => {
    const cleanedId = id.trim();
    if (!cleanedId) return showToast('Enter a public endpoint ID.');
    setPublicLoading(true); setPublicData(null);
    try {
      const data = await apiRequest(`/api/public/${encodeURIComponent(cleanedId)}`);
      setPublicData(data); setPublicId(cleanedId);
    } catch (error) { showToast(`Could not load public endpoint: ${error.message}`); }
    finally { setPublicLoading(false); }
  };

  const copyText = async (text) => {
    try { await navigator.clipboard.writeText(text); showToast('Copied to clipboard.'); }
    catch { showToast('Clipboard access failed. Copy the URL manually.'); }
  };

  const navItems = [
    { id: 'check', label: 'Check metadata', icon: FileSearch },
    { id: 'clean', label: 'Clean metadata', icon: Sparkles },
    { id: 'endpoints', label: 'My endpoints', icon: Code2, protected: true },
    { id: 'activity', label: 'Activity history', icon: Activity, protected: true },
    { id: 'public', label: 'Public endpoint', icon: CloudUpload },
  ];

  const changeTab = (id) => setActiveTab(id);

  const screenProps = {
    activeTab, PageHeading, ImageWorkspace, SignInCard, EmptyState, EndpointCard,
    selectedFile, previewUrl, chooseFile, busy, checkMetadata, checkResult,
    removeSelectedFile, loadSampleImage, showToast, cleanMetadata, cleaningMode, lastClean,
    verifyCleanedFile, token, endpoints, newEndpointName, setNewEndpointName,
    createEndpoint, editingId, editingName, setEditingId, setEditingName,
    saveEndpointName, deleteEndpoint, endpointFiles, setEndpointFiles,
    endpointModes, setEndpointModes, uploadEndpointImage, uploadingEndpoint,
    copyText, activities, refreshAccountData, publicId, setPublicId,
    loadPublicEndpoint, publicLoading, publicData, apiUrl, deleteEndpointImage,
    formatDate,
  };

  return (
    <div className="app-shell">
      <main className="main-area">
        <header className="topbar">
          <img className="topbar-logo" src={theme === 'dark' ? metaCleanLogoDark : metaCleanLogoLight} alt="MetaClean" />
          <MainNavigation items={navItems} activePage={activeTab} isSignedIn={Boolean(token)} onNavigate={changeTab} />
          <HeaderActions
            theme={theme}
            onToggleTheme={() => setTheme(theme === 'light' ? 'dark' : 'light')}
            onRefresh={checkHealth}
            user={user}
            onSignOut={signOut}
            clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}
            onLoginSuccess={onLoginSuccess}
            onLoginError={() => showToast('Google sign-in failed. Please try again.')}
          />
        </header>

        <div className="page-content">
          <CheckMetadataScreen {...screenProps} />
          <CleanMetadataScreen {...screenProps} />
          <EndpointsScreen {...screenProps} />
          <ActivityScreen {...screenProps} />
          <PublicEndpointScreen {...screenProps} />

          <footer className="footer">
            <span>MetaClean <span className="footer-dot">·</span> Intelligent image metadata detector</span>
          </footer>
        </div>
      </main>

      {toast && (
        <div className="toast" role="status">
          <AlertCircle size={17} />
          <span>{toast}</span>
          <button onClick={() => setToast('')} aria-label="Dismiss message"><X size={15} /></button>
        </div>
      )}
    </div>
  );
}

// Used only to show the Google account name while the server loads its account
// record. Protected API requests still rely on server-side token verification.
function readGoogleProfile(credential) {
  try {
    const payload = credential.split('.')[1];
    if (!payload) return null;
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const claims = JSON.parse(atob(base64));
    return { name: claims.name, email: claims.email, picture: claims.picture };
  } catch {
    return null;
  }
}




export default App;

