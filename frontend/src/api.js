// For local development, leave this empty to use Vite's /api proxy. On Vercel,
// set VITE_API_BASE_URL to the deployed Render backend URL.
const configuredApiBase = import.meta.env.VITE_API_BASE_URL || '';
const API_BASE = configuredApiBase.replace(/^(https?:\/\/)(localhost|127\.0\.0\.1)(?=[:/]|$)/, `$1${window.location.hostname}`).replace(/\/$/, '');

export function apiUrl(path) {
  if (!path) return API_BASE;
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_BASE}${path.startsWith('/') ? '' : '/'}${path}`;
}

async function readError(response) {
  const type = response.headers.get('content-type') || '';
  if (type.includes('application/json')) {
    const body = await response.json().catch(() => ({}));
    if (typeof body.detail === 'string') return body.detail;
    if (body.detail) return JSON.stringify(body.detail);
    return JSON.stringify(body);
  }
  return (await response.text().catch(() => '')) || `Request failed (${response.status})`;
}

export async function apiRequest(path, options = {}, token = null) {
  const headers = new Headers(options.headers || {});
  if (token) headers.set('Authorization', `Bearer ${token}`);
  // Do not set Content-Type for FormData; the browser must add its multipart boundary.
  if (token === 'cookie-session') headers.delete('Authorization');
  const response = await fetch(apiUrl(path), { ...options, headers, credentials: 'include' });
  if (!response.ok) throw new Error(await readError(response));
  if (response.status === 204) return null;
  const type = response.headers.get('content-type') || '';
  if (type.includes('application/json')) return response.json();
  return response;
}

export async function apiDownload(path, formData, token = null) {
  const headers = {};
  if (token && token !== 'cookie-session') headers.Authorization = `Bearer ${token}`;
  const response = await fetch(apiUrl(path), { method: 'POST', headers, body: formData, credentials: 'include' });
  if (!response.ok) throw new Error(await readError(response));
  const disposition = response.headers.get('content-disposition') || '';
  const match = disposition.match(/filename\*?=(?:UTF-8''|\")?([^\";]+)/i);
  const filename = match ? decodeURIComponent(match[1].replace(/"/g, '')) : 'image-cleaned';
  return { blob: await response.blob(), filename };
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
}
