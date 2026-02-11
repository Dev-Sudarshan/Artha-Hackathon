import axios from 'axios';

// Allow overriding the backend URL via env; fall back to local dev port 8000
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// ---- In-memory token cache (avoids JSON.parse on every request) ----
let _cachedToken = null;

export function setCachedToken(token) {
    _cachedToken = token;
}

// Hydrate token from localStorage once on load
try {
    const stored = localStorage.getItem('artha_user');
    if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed?.token) _cachedToken = parsed.token;
    }
} catch { /* ignore */ }

// Request Interceptor: Attach Token (from memory, no JSON.parse)
api.interceptors.request.use(
    (config) => {
        if (_cachedToken) {
            config.headers.Authorization = `Bearer ${_cachedToken}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response Interceptor: Handle Auth Errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // Token expired or invalid
            _cachedToken = null;
            localStorage.removeItem('artha_user');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default api;
