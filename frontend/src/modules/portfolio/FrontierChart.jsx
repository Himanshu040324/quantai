// frontend/src/modules/portfolio/FrontierChart.jsx
// NEW FILE
//
// Scatter plot of the Efficient Frontier (variance on x, return on y —
// the conventional orientation), with the risk_lambda-based recommended
// portfolio marked as a distinct point.

import {
  CartesianGrid,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ResponsiveContainer,
} from 'recharts';

function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-sm shadow-lg">
      <p className="text-text-muted">Return: {formatPercent(point.target_return)}</p>
      <p className="text-text-muted">
        Volatility: {formatPercent(Math.sqrt(point.expected_variance))}
      </p>
    </div>
  );
}

export default function FrontierChart({ frontier, recommended }) {
  const frontierPoints = frontier.map((p) => ({
    target_return: p.target_return,
    expected_variance: p.expected_variance,
    volatility: Math.sqrt(p.expected_variance),
  }));

  const recommendedPoint = [
    {
      target_return: recommended.expected_return,
      expected_variance: recommended.expected_variance,
      volatility: Math.sqrt(recommended.expected_variance),
    },
  ];

  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="mb-2 text-sm text-text-muted">
        Efficient Frontier — each point is a portfolio with minimum risk for its return level.
        The highlighted point is your recommended allocation.
      </p>
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
            <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" />
            <XAxis
              type="number"
              dataKey="volatility"
              name="Volatility"
              tickFormatter={formatPercent}
              stroke="var(--color-text-muted)"
              label={{
                value: 'Volatility (risk)',
                position: 'insideBottom',
                offset: -5,
                fill: 'var(--color-text-muted)',
              }}
            />
            <YAxis
              type="number"
              dataKey="target_return"
              name="Expected Return"
              tickFormatter={formatPercent}
              stroke="var(--color-text-muted)"
              label={{
                value: 'Expected Return',
                angle: -90,
                position: 'insideLeft',
                fill: 'var(--color-text-muted)',
              }}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
            <Scatter data={frontierPoints} fill="var(--color-secondary)" line shape="circle" />
            <Scatter data={recommendedPoint} fill="var(--color-math)" shape="star" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}