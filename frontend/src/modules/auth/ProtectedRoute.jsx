// frontend/src/modules/auth/ProtectedRoute.jsx
// NEW FILE

import { Navigate } from 'react-router-dom';
import { useAuth } from './authContext';

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    // Avoid a flash-redirect to /login while the silent refresh
    // attempt is still in flight on page load.
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-text-muted">
        Loading...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}