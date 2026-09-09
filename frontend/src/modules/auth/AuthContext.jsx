// frontend/src/modules/auth/AuthContext.jsx
// REPLACING EXISTING FILE
//
// Exports ONLY the AuthProvider component now. The context object and
// useAuth hook moved to authContext.js so this file satisfies
// react-refresh/only-export-components (a file with Fast Refresh must
// export components only, nothing else).

import { useEffect, useState, useCallback } from 'react';
import apiClient, { setAccessToken } from '../../lib/apiClient';
import { AuthContext } from './authContext.js';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  // isLoading covers the initial silent-refresh attempt on page load,
  // so ProtectedRoute doesn't redirect to /login before we've even
  // checked whether a valid refresh cookie exists.
  const [isLoading, setIsLoading] = useState(true);

  const fetchProfile = useCallback(async () => {
    const res = await apiClient.get('/api/users/profile');
    setUser(res.data.user);
    return res.data.user;
  }, []);

  // On first mount, try to silently restore the session using the
  // httpOnly refresh cookie (if the user was already logged in from a
  // previous visit). If there's no valid cookie, this just fails
  // quietly and the user lands on the login page.
  useEffect(() => {
    let cancelled = false;

    async function tryRestoreSession() {
      try {
        const res = await apiClient.post('/api/auth/refresh');
        setAccessToken(res.data.accessToken);
        if (!cancelled) await fetchProfile();
      } catch {
        // No valid refresh cookie — user needs to log in. Not an error.
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    tryRestoreSession();
    return () => {
      cancelled = true;
    };
  }, [fetchProfile]);

  const signup = useCallback(async (formData) => {
    const res = await apiClient.post('/api/auth/signup', formData);
    setAccessToken(res.data.accessToken);
    setUser(res.data.user);
    return res.data.user;
  }, []);

  const login = useCallback(async (email, password) => {
    const res = await apiClient.post('/api/auth/login', { email, password });
    setAccessToken(res.data.accessToken);
    setUser(res.data.user);
    return res.data.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiClient.post('/api/auth/logout');
    } finally {
      setAccessToken(null);
      setUser(null);
    }
  }, []);

  const refreshProfile = useCallback(async () => {
    return fetchProfile();
  }, [fetchProfile]);

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    signup,
    login,
    logout,
    refreshProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}