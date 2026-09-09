// frontend/src/modules/portfolio/DashboardPage.jsx
// NEW FILE

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useAuth } from '../auth/authContext'

// Dummy data only to confirm the charting pipeline renders end-to-end,
// per Phase 1's exit criteria. Phase 2 replaces this with real cached
// price history from the FastAPI data pipeline.
const DUMMY_CHART_DATA = [
  { date: 'Mon', value: 100000 },
  { date: 'Tue', value: 100850 },
  { date: 'Wed', value: 99420 },
  { date: 'Thu', value: 101200 },
  { date: 'Fri', value: 102750 },
];

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

        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-medium text-text-main">Portfolio Value</h2>
            <span className="rounded-full bg-math/20 px-2 py-0.5 text-xs font-medium text-math">
              Placeholder data
            </span>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={DUMMY_CHART_DATA}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  color: '#f8fafc',
                }}
              />
              <Line type="monotone" dataKey="value" stroke="#2e74b5" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
          <p className="mt-2 text-xs text-text-muted">
            This chart uses placeholder data to confirm the charting pipeline works. Phase 2 wires in
            real cached price history.
          </p>
        </div>
      </div>
    </div>
  );
}
