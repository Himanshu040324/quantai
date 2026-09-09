// frontend/src/lib/apiClient.js
// NEW FILE

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// withCredentials is required so the browser sends/receives the
// httpOnly refresh cookie set by backend/src/modules/auth. Without
// this, POST /api/auth/refresh will never see the cookie.
const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
});

// Access token is held in memory only (never localStorage), set by
// AuthContext after login/signup/refresh. A plain module-level
// variable is fine here since this file is a singleton per page load.
let accessToken = null;

export function setAccessToken(token) {
  accessToken = token;
}

apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// If a request fails with 401, try refreshing the access token once
// via the httpOnly cookie, then retry the original request. If the
// refresh itself fails, give up and let the caller (AuthContext) log
// the user out.
let refreshPromise = null;

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/api/auth/refresh')
    ) {
      originalRequest._retry = true;

      try {
        // De-duplicate concurrent refresh calls if multiple requests
        // 401 at the same time.
        if (!refreshPromise) {
          refreshPromise = apiClient
            .post('/api/auth/refresh')
            .then((res) => {
              setAccessToken(res.data.accessToken);
              return res.data.accessToken;
            })
            .finally(() => {
              refreshPromise = null;
            });
        }
        const newToken = await refreshPromise;
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        setAccessToken(null);
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;