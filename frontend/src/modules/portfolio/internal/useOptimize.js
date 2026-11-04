// frontend/src/modules/portfolio/internal/useOptimize.js
// NEW FILE
//
// Fetch hook for POST /optimize and POST /optimize/cvar — both are
// on-demand (triggered by user action, not on mount), so this hook
// exposes a `run(strategy)` function rather than auto-fetching.
//
// Derived-state pattern (requestKey vs settledKey), same principle
// documented for useOhlcv.js in the Phase 2 summary: setState only
// ever happens inside .then/.catch, never synchronously in an effect
// body, so a superseded request can't flash stale data over a newer one.

import { useCallback, useRef, useState } from 'react';
import apiClient from '../../../lib/apiClient';

const ENDPOINTS = {
  markowitz: '/api/ai-gateway/optimize',
  cvar: '/api/ai-gateway/optimize/cvar',
};

export function useOptimize() {
  const [status, setStatus] = useState('idle'); // idle | loading | success | error
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [strategy, setStrategy] = useState(null);

  // Monotonically increasing request id — only the response matching
  // the latest requestIdRef.current is allowed to update state, so a
  // slow superseded request can never overwrite a newer result.
  const requestIdRef = useRef(0);

  const run = useCallback(async (requestedStrategy) => {
    const endpoint = ENDPOINTS[requestedStrategy];
    if (!endpoint) {
      throw new Error(`Unknown optimization strategy: ${requestedStrategy}`);
    }

    const thisRequestId = ++requestIdRef.current;
    setStatus('loading');
    setStrategy(requestedStrategy);

    try {
      const response = await apiClient.post(endpoint, {});
      if (requestIdRef.current !== thisRequestId) return; // superseded, ignore
      setData(response.data);
      setError(null);
      setStatus('success');
    } catch (err) {
      if (requestIdRef.current !== thisRequestId) return; // superseded, ignore
      setData(null);
      setError(
        err.response?.data?.errors?.[0] ||
          err.response?.data?.detail ||
          'Failed to compute allocation. Please try again.'
      );
      setStatus('error');
    }
  }, []);

  return { status, data, error, strategy, run };
}