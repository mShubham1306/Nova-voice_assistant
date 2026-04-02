/**
 * NOVA API Service - Handles all backend communication
 */

const API_BASE = '/api';

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
  getStatus: () => fetchAPI('/status'),
  startAssistant: () => fetchAPI('/start', { method: 'POST' }),
  stopAssistant: () => fetchAPI('/stop', { method: 'POST' }),
  sendCommand: (query) => fetchAPI('/command', {
    method: 'POST',
    body: JSON.stringify({ query }),
  }),
  getHistory: () => fetchAPI('/history'),
  getFeatures: () => fetchAPI('/features'),
  toggleWakeWord: () => fetchAPI('/wake-word', { method: 'POST' }),
};

export default api;
