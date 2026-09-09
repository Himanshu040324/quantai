// frontend/src/modules/auth/LoginPage.jsx
// NEW FILE

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from './authContext';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setErrors([]);
    setIsSubmitting(true);

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      const apiErrors = err.response?.data?.errors;
      setErrors(apiErrors?.length ? apiErrors : ['Something went wrong. Please try again.']);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md rounded-lg border border-border bg-surface p-8">
        <h1 className="mb-1 text-2xl font-semibold text-text-main">Welcome back</h1>
        <p className="mb-6 text-sm text-text-muted">Log in to view your portfolio.</p>

        {errors.length > 0 && (
          <div className="mb-4 rounded-md border border-error/40 bg-error/10 p-3 text-sm text-error">
            {errors.map((err) => (
              <p key={err}>{err}</p>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm text-text-muted" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-text-main outline-none focus:border-secondary"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm text-text-muted" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-text-main outline-none focus:border-secondary"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-md bg-primary py-2 font-medium text-text-main transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {isSubmitting ? 'Logging in...' : 'Log in'}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-text-muted">
          Don&apos;t have an account?{' '}
          <Link to="/signup" className="text-secondary hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}