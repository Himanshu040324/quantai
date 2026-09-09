// frontend/src/App.jsx
// REPLACING EXISTING FILE

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './modules/auth/AuthContext.jsx';
import ProtectedRoute from './modules/auth/ProtectedRoute';
import LoginPage from './modules/auth/LoginPage';
import SignupPage from './modules/auth/SignupPage';
import DashboardPage from './modules/portfolio/DashboardPage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

