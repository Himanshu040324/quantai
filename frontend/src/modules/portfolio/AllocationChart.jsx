// frontend/src/modules/portfolio/AllocationChart.jsx
// NEW FILE
//
// Pie chart of a single strategy's allocation weights. Strategy-
// agnostic — receives allocations + summary stats as props, doesn't
// know or care whether they came from Markowitz or CVaR.

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

// Distinct per-slice colors, generated around the Math accent token
// so slices are distinguishable while staying in the project's dark
// palette. Recharts needs literal hex per Cell — CSS variables aren't
// resolvable inside SVG fill props reliably across browsers, so this
// is the one place a fixed palette is declared rather than referencing
// --color-math directly for every slice.
const SLICE_COLORS = [
  '#1f7a3d', '#2e74b5', '#22c55e', '#94a3b8',
  '#b85c00', '#6a1b9a', '#eab308', '#334155',
];

function formatPercent(weight) {
  return `${(weight * 100).toFixed(1)}%`;
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { ticker, weight } = payload[0].payload;
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-sm shadow-lg">
      <p className="font-medium text-text-main">{ticker}</p>
      <p className="text-text-muted">{formatPercent(weight)}</p>
    </div>
  );
}

export default function AllocationChart({ allocations, expectedReturn, expectedVariance }) {
  const nonZero = allocations.filter((a) => a.weight > 0.0001);
  const expectedVolatility = Math.sqrt(expectedVariance);

  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="mb-4 flex flex-wrap gap-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-text-muted">Expected Return</p>
          <p className="text-lg font-semibold text-math">{formatPercent(expectedReturn)}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-text-muted">Expected Volatility</p>
          <p className="text-lg font-semibold text-text-main">{formatPercent(expectedVolatility)}</p>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={nonZero}
              dataKey="weight"
              nameKey="ticker"
              cx="50%"
              cy="50%"
              outerRadius={100}
              label={({ ticker, weight }) => `${ticker} ${formatPercent(weight)}`}
              labelLine={false}
            >
              {nonZero.map((entry, index) => (
                <Cell key={entry.ticker} fill={SLICE_COLORS[index % SLICE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}