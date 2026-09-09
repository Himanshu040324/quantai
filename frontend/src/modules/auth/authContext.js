// frontend/src/modules/auth/authContext.js
// NEW FILE
//
// Holds ONLY the context object and the useAuth hook — no component
// export. Split out of AuthContext.jsx to satisfy
// react-refresh/only-export-components: a file that mixes component
// and non-component exports breaks Vite Fast Refresh (you get full
// page reloads instead of hot updates during dev).

import { createContext, useContext } from 'react';

export const AuthContext = createContext(null);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}