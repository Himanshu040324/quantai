// frontend/src/modules/auth/SignupPage.jsx
// NEW FILE

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from './authContext';

const RISK_OPTIONS = [
  { value: 'conservative', label: 'Conservative' },
  { value: 'moderate', label: 'Moderate' },
  { value: 'aggressive', label: 'Aggressive' },
];

export default function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: '',
    password: '',
    capitalDisplay: '', // user enters major units (e.g. rupees), we convert to paise below
    timeHorizonYears: '',
    riskLabel: 'moderate',
  });
  const [errors, setErrors] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function updateField(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setErrors([]);
    setIsSubmitting(true);

    try {
      // Convert user-entered major units to the smallest currency unit
      // (integer) before sending, per the monetary integrity rule —
      // the backend rejects non-integer capital outright.
      const capital = Math.round(parseFloat(form.capitalDisplay) * 100);

      await signup({
        email: form.email,
        password: form.password,
        capital,
        timeHorizonYears: parseInt(form.timeHorizonYears, 10),
        riskLabel: form.riskLabel,
      });
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
        <h1 className="mb-1 text-2xl font-semibold text-text-main">Create your account</h1>
        <p className="mb-6 text-sm text-text-muted">
          Tell us a bit about your investing goals to get started.
        </p>

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
              value={form.email}
              onChange={(e) => updateField('email', e.target.value)}
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
              minLength={8}
              value={form.password}
              onChange={(e) => updateField('password', e.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-text-main outline-none focus:border-secondary"
            />
            <p className="mt-1 text-xs text-text-muted">At least 8 characters, with a letter and a number.</p>
          </div>

          <div>
            <label className="mb-1 block text-sm text-text-muted" htmlFor="capital">
              Starting capital
            </label>
            <input
              id="capital"
              type="number"
              min="0"
              step="0.01"
              required
              value={form.capitalDisplay}
              onChange={(e) => updateField('capitalDisplay', e.target.value)}
              placeholder="e.g. 50000"
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-text-main outline-none focus:border-secondary"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm text-text-muted" htmlFor="horizon">
              Time horizon (years)
            </label>
            <input
              id="horizon"
              type="number"
              min="1"
              max="50"
              step="1"
              required
              value={form.timeHorizonYears}
              onChange={(e) => updateField('timeHorizonYears', e.target.value)}
              placeholder="e.g. 5"
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-text-main outline-none focus:border-secondary"
            />
          </div>

          <div>
            <span className="mb-1 block text-sm text-text-muted">Risk appetite</span>
            <div className="flex gap-2">
              {RISK_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => updateField('riskLabel', opt.value)}
                  className={`flex-1 rounded-md border px-3 py-2 text-sm transition-colors ${
                    form.riskLabel === opt.value
                      ? 'border-secondary bg-secondary/20 text-text-main'
                      : 'border-border text-text-muted hover:border-secondary/50'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-md bg-primary py-2 font-medium text-text-main transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {isSubmitting ? 'Creating account...' : 'Sign up'}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-text-muted">
          Already have an account?{' '}
          <Link to="/login" className="text-secondary hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}