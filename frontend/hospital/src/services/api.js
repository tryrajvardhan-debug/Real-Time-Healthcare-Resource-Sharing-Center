import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

const ACCESS_KEYS = ['access_token', 'medgrid_access_token'];
const REFRESH_KEYS = ['refresh_token', 'medgrid_refresh_token'];

const getFirstStorageValue = (keys) => {
  for (const k of keys) {
    const v = localStorage.getItem(k);
    if (v) return v;
  }
  return null;
};

const setTokenPair = ({ access, refresh }) => {
  if (access) {
    localStorage.setItem('access_token', access);
    localStorage.setItem('medgrid_access_token', access);
  }
  if (refresh) {
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('medgrid_refresh_token', refresh);
  }
};

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = getFirstStorageValue(ACCESS_KEYS);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let isRefreshing = false;
let refreshQueue = [];

const resolveQueue = (error, accessToken = null) => {
  refreshQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve(accessToken);
  });
  refreshQueue = [];
};

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;
    if (!err.response || err.response.status !== 401 || original?._retry) {
      return Promise.reject(err);
    }

    const refresh = getFirstStorageValue(REFRESH_KEYS);
    if (!refresh) return Promise.reject(err);

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push({
          resolve: (accessToken) => {
            original.headers.Authorization = `Bearer ${accessToken}`;
            resolve(api(original));
          },
          reject,
        });
      });
    }

    original._retry = true;
    isRefreshing = true;

    try {
      const refreshRes = await axios.post(`${API_BASE_URL}/api/auth/token/refresh/`, { refresh }, { headers: { 'Content-Type': 'application/json' } });
      const newAccess = refreshRes.data?.access;
      const newRefresh = refreshRes.data?.refresh;
      setTokenPair({ access: newAccess, refresh: newRefresh });
      resolveQueue(null, newAccess);
      original.headers.Authorization = `Bearer ${newAccess}`;
      return api(original);
    } catch (refreshErr) {
      resolveQueue(refreshErr, null);
      return Promise.reject(refreshErr);
    } finally {
      isRefreshing = false;
    }
  }
);

/**
 * Backwards-compatible wrapper around Axios for existing code that expects:
 * - `res.ok`
 * - `await res.json()`
 * - `res.status`
 */
export const apiFetch = async (endpoint, options = {}) => {
  const method = (options.method || 'GET').toUpperCase();
  const headers = options.headers || {};
  let data = undefined;
  if (options.body !== undefined) {
    try {
      data = typeof options.body === 'string' ? JSON.parse(options.body) : options.body;
    } catch {
      data = options.body;
    }
  }

  try {
    const res = await api.request({ url: endpoint, method, data, headers });
    return {
      ok: true,
      status: res.status,
      json: async () => res.data,
    };
  } catch (e) {
    const status = e.response?.status ?? 0;
    const payload = e.response?.data ?? { detail: e.message || 'Request failed' };
    return {
      ok: false,
      status,
      json: async () => payload,
    };
  }
};

export default apiFetch;
