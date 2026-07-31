/**
 * NOVA API Service — Handles all backend communication.
 *
 * In development (Vite dev server):
 *   VITE_API_URL is not set → API_BASE = '/api' → proxied to localhost:5000
 *
 * In production (Vercel frontend + Render backend):
 *   VITE_API_URL = 'https://your-nova-backend.onrender.com'
 *   API_BASE = 'https://your-nova-backend.onrender.com/api'
 */

const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api';

async function fetchAPI(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    if (!response.ok) throw new Error(`API Error: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error(`[API] ${endpoint}:`, error);
    throw error;
  }
}

export const api = {
  getStatus:       () => fetchAPI('/status'),
  startAssistant:  () => fetchAPI('/start', { method: 'POST' }),
  stopAssistant:   () => fetchAPI('/stop',  { method: 'POST' }),
  sendCommand:     (query) => fetchAPI('/command', {
    method: 'POST',
    body: JSON.stringify({ query }),
  }),
  getHistory:      () => fetchAPI('/history'),
  getFeatures:     () => fetchAPI('/features'),
  toggleWakeWord:  () => fetchAPI('/wake-word', { method: 'POST' }),
};

export default api;
