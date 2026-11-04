// frontend/src/modules/portfolio/internal/useFrontier.js
// NEW FILE
//
// Separate hook from useOptimize — the frontier is a distinct,
// heavier fetch (sweeps ~25 QP solves server-side) only needed when
// the user opens the frontier view, not bundled into every
// Markowitz/CVaR call.

import { useCallback, useRef, useState } from 'react';
import apiClient from '../../../lib/apiClient';

export function useFrontier() {
  const [status, setStatus] = useState('idle'); // idle | loading | success | error
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const requestIdRef = useRef(0);

  const run = useCallback(async (numPoints = 25) => {
    const thisRequestId = ++requestIdRef.current;
    setStatus('loading');

    try {
      const response = await apiClient.post('/api/ai-gateway/optimize/frontier', {
        num_points: numPoints,
      });
      if (requestIdRef.current !== thisRequestId) return;
      setData(response.data);
      setError(null);
      setStatus('success');
    } catch (err) {
      if (requestIdRef.current !== thisRequestId) return;
      setData(null);
      setError(
        err.response?.data?.errors?.[0] ||
          err.response?.data?.detail ||
          'Failed to compute the efficient frontier. Please try again.'
      );
      setStatus('error');
    }
  }, []);

  return { status, data, error, run };
}