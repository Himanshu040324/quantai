// frontend/src/modules/portfolio/OptimizationPanel.jsx
// NEW FILE
//
// Top-level Phase 3 UI: tab toggle between Markowitz/CVaR, an on-demand
// "Compute" trigger per tab (per Himanshu's call — no auto-fetch on
// mount), loading/error states, and a separate on-demand frontier view.
// Composes AllocationChart + FrontierChart; owns no optimization math
// itself — purely presentational + the two fetch hooks.

import { useState } from 'react';
import AllocationChart from './AllocationChart';
import FrontierChart from './FrontierChart';
import { useOptimize } from './internal/useOptimize';
import { useFrontier } from './internal/useFrontier';

const STRATEGY_TABS = [
  { key: 'markowitz', label: 'Markowitz', accentClass: 'border-math text-math' },
  { key: 'cvar', label: 'CVaR', accentClass: 'border-genai text-genai' },
];

function TabButton({ tab, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-t-md border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
        active
          ? tab.accentClass
          : 'border-transparent text-text-muted hover:text-text-main'
      }`}
    >
      {tab.label}
    </button>
  );
}

function ErrorBanner({ message }) {
  return (
    <div className="rounded-md border border-error bg-error/10 px-4 py-3 text-sm text-error">
      {message}
    </div>
  );
}

export default function OptimizationPanel() {
  const [activeTab, setActiveTab] = useState('markowitz');
  const [showFrontier, setShowFrontier] = useState(false);

  const optimize = useOptimize();
  const frontier = useFrontier();

  const handleCompute = () => {
    optimize.run(activeTab);
  };

  const handleToggleFrontier = () => {
    if (!showFrontier && frontier.status === 'idle') {
      frontier.run();
    }
    setShowFrontier((prev) => !prev);
  };

  // The fetched result belongs to whichever strategy was last requested —
  // if the user switches tabs without re-computing, don't show the
  // previous tab's numbers under the new tab's label.
  const resultMatchesActiveTab = optimize.strategy === activeTab;

  return (
    <div className="mt-8">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text-main">Portfolio Optimization</h2>
        <button
          onClick={handleToggleFrontier}
          className="rounded-md border border-border px-3 py-1.5 text-sm text-text-muted transition-colors hover:border-secondary hover:text-secondary"
        >
          {showFrontier ? 'Hide' : 'Show'} Efficient Frontier
        </button>
      </div>

      <div className="flex gap-1 border-b border-border">
        {STRATEGY_TABS.map((tab) => (
          <TabButton
            key={tab.key}
            tab={tab}
            active={activeTab === tab.key}
            onClick={() => setActiveTab(tab.key)}
          />
        ))}
      </div>

      <div className="mt-4 space-y-4">
        <button
          onClick={handleCompute}
          disabled={optimize.status === 'loading'}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-text-main transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {optimize.status === 'loading'
            ? 'Computing...'
            : `Compute ${activeTab === 'markowitz' ? 'Markowitz' : 'CVaR'} Allocation`}
        </button>

        {optimize.status === 'error' && <ErrorBanner message={optimize.error} />}

        {optimize.status === 'success' && resultMatchesActiveTab && (
          <AllocationChart
            allocations={optimize.data.allocations}
            expectedReturn={optimize.data.expected_return}
            expectedVariance={optimize.data.expected_variance}
          />
        )}

        {optimize.status === 'success' && resultMatchesActiveTab && activeTab === 'cvar' && (
          <p className="text-sm text-text-muted">
            CVaR (95% confidence): {(optimize.data.cvar * 100).toFixed(2)}% expected loss in
            worst-case scenarios
          </p>
        )}

        {showFrontier && (
          <>
            {frontier.status === 'loading' && (
              <p className="text-sm text-text-muted">Computing efficient frontier...</p>
            )}
            {frontier.status === 'error' && <ErrorBanner message={frontier.error} />}
            {frontier.status === 'success' && (
              <FrontierChart frontier={frontier.data.frontier} recommended={frontier.data.recommended} />
            )}
          </>
        )}
      </div>
    </div>
  );
}