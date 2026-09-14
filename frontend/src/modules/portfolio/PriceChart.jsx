// frontend/src/modules/portfolio/PriceChart.jsx
// NEW FILE

import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TICKER_UNIVERSE } from './internal/tickerUniverse';
import { useOhlcv } from './internal/useOhlcv';

function formatDate(isoDate) {
  return new Date(isoDate).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export default function PriceChart() {
  const [selectedTicker, setSelectedTicker] = useState(TICKER_UNIVERSE[0].ticker);
  const { bars, source, status, errorMessage } = useOhlcv(selectedTicker, 1);

  const chartData = bars.map((bar) => ({
    date: bar.date,
    displayDate: formatDate(bar.date),
    close: bar.close,
  }));

  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-medium text-text-main">Price History</h2>

        <div className="flex items-center gap-3">
          {status === 'success' && (
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                source === 'cache' ? 'bg-secondary/20 text-secondary' : 'bg-math/20 text-math'
              }`}
            >
              {source === 'cache' ? 'From cache' : 'Live fetch'}
            </span>
          )}
          <select
            value={selectedTicker}
            onChange={(e) => setSelectedTicker(e.target.value)}
            className="rounded-md border border-border bg-background px-3 py-1.5 text-sm text-text-main focus:border-secondary focus:outline-none"
          >
            {TICKER_UNIVERSE.map((t) => (
              <option key={t.ticker} value={t.ticker}>
                {t.label} ({t.ticker})
              </option>
            ))}
          </select>
        </div>
      </div>

      {status === 'loading' && (
        <div className="flex h-70 items-center justify-center text-sm text-text-muted">
          Loading price data…
        </div>
      )}

      {status === 'error' && (
        <div className="flex h-70 flex-col items-center justify-center gap-2 text-center">
          <p className="text-sm text-error">{errorMessage}</p>
          <p className="text-xs text-text-muted">Try selecting a different ticker, or refresh the page.</p>
        </div>
      )}

      {status === 'success' && chartData.length === 0 && (
        <div className="flex h-70 items-center justify-center text-sm text-text-muted">
          No price data available for this ticker.
        </div>
      )}

      {status === 'success' && chartData.length > 0 && (
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="displayDate" stroke="#94a3b8" fontSize={12} />
            <YAxis stroke="#94a3b8" fontSize={12} domain={['auto', 'auto']} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '6px',
                color: '#f8fafc',
              }}
              labelFormatter={(label, payload) => payload?.[0]?.payload?.date || label}
              formatter={(value) => [value.toFixed(2), 'Close']}
            />
            <Line type="monotone" dataKey="close" stroke="#2e74b5" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )}

      <p className="mt-2 text-xs text-text-muted">
        1-year daily close price, served from QuantAI's cached market data pipeline.
      </p>
    </div>
  );
}