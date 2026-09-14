// frontend/src/modules/portfolio/internal/useOhlcv.js
// REPLACING EXISTING FILE
//
// Data-fetching hook, separated from PriceChart.jsx's rendering.
//
// Loading state is DERIVED, not stored: we track which request last
// settled (settledKey) and compare it against the current request
// (requestKey) during render. If they don't match, we're loading —
// no setState call is needed just to announce "a fetch started."
// setState only happens inside .then/.catch, which are async
// callbacks, not synchronous effect-body code — this is what
// react-hooks/set-state-in-effect wants: effects should synchronize
// with external systems and update state from their callbacks, not
// eagerly setState the moment the effect runs.

import { useEffect, useState } from "react";
import apiClient from "../../../lib/apiClient";

export function useOhlcv(ticker, years = 1) {
  const requestKey = ticker ? `${ticker}:${years}` : null;

  // Everything that results from a settled request lives in one
  // object, written exactly once per request (in .then or .catch) —
  // no separate setStatus/setBars/setSource/setErrorMessage calls
  // that could land in different renders.
  const [result, setResult] = useState({
    key: null,
    bars: [],
    source: null,
    errorMessage: null,
  });

  useEffect(() => {
    if (!requestKey) return;

    let cancelled = false;

    apiClient
      .get(`/api/ai-gateway/market-data/ohlcv/${encodeURIComponent(ticker)}`, {
        params: { years },
      })
      .then((res) => {
        if (cancelled) return;
        setResult({
          key: requestKey,
          bars: res.data.bars,
          source: res.data.source,
          errorMessage: null,
        });
      })
      .catch((err) => {
        if (cancelled) return;
        // 502 from ai-gateway means ai-service itself is unreachable
        // (Step 6's AiServiceUnavailableError) — surface that
        // distinctly from a generic fetch failure.
        const isServiceDown = err.response?.status === 502;
        setResult({
          key: requestKey,
          bars: [],
          source: null,
          errorMessage: isServiceDown
            ? "The market data service is temporarily unavailable. Please try again shortly."
            : err.response?.data?.errors?.[0] || "Failed to load price data.",
        });
      });

    return () => {
      cancelled = true;
    };
  }, [requestKey, ticker, years]);

  // Derived at render time: if the last-settled result's key doesn't
  // match what we're currently supposed to be showing, we're loading
  // — no matter whether that's the very first request or a ticker
  // switch mid-flight.
  const isCurrent = result.key === requestKey;
  const status = !requestKey
    ? "idle"
    : !isCurrent
      ? "loading"
      : result.errorMessage
        ? "error"
        : "success";

  return {
    bars: isCurrent ? result.bars : [],
    source: isCurrent ? result.source : null,
    status,
    errorMessage: isCurrent ? result.errorMessage : null,
  };
}
