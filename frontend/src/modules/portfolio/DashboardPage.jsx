// frontend/src/modules/portfolio/DashboardPage.jsx
// REPLACING EXISTING FILE

import { useAuth } from '../auth/authContext';
import PriceChart from './PriceChart';

const RISK_LABEL_DISPLAY = {
  conservative: 'Conservative',
  moderate: 'Moderate',
  aggressive: 'Aggressive',
};

function formatCurrency(paise) {
  // capital is stored as an integer in the smallest unit (paise);
  // convert to major units only for display, never for storage/math.
  return (paise / 100).toLocaleString(undefined, {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  });
}

function StatCard({ label, value, accent }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="text-sm text-text-muted">{label}</p>
      <p className={`mt-1 text-xl font-semibold ${accent ? 'text-secondary' : 'text-text-main'}`}>
        {value}
      </p>
    </div>
  );
}

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-background px-6 py-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-text-main">Dashboard</h1>
            <p className="text-sm text-text-muted">{user?.email}</p>
          </div>
          <button
            onClick={logout}
            className="rounded-md border border-border px-4 py-2 text-sm text-text-muted transition-colors hover:border-error hover:text-error"
          >
            Log out
          </button>
        </div>

        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard label="Capital" value={user ? formatCurrency(user.capital) : '—'} />
          <StatCard
            label="Time Horizon"
            value={user ? `${user.timeHorizonYears} year${user.timeHorizonYears === 1 ? '' : 's'}` : '—'}
          />
          <StatCard
            label="Risk Appetite"
            value={user ? RISK_LABEL_DISPLAY[user.riskLabel] : '—'}
            accent
          />
        </div>

        <PriceChart />
      </div>
    </div>
  );
}