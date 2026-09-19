// backend/src/modules/ai-gateway/index.js
// REPLACING EXISTING FILE
//
// PUBLIC CONTRACT for the ai-gateway module.
// Other modules must import ONLY from this file — never reach into
// ai-gateway/internal/* directly. Mirrors auth/index.js's pattern of
// building the router right here rather than in a separate file.

const express = require('express');
const { requireAuth } = require('../auth'); // cross-module import via auth's public contract
const {
  getOhlcv,
  fetchOhlcvUniverse,
  getFundamentals,
  fetchFundamentalsUniverse,
  getNews,
  fetchNewsUniverse,
  getOptimalAllocation,
  getEfficientFrontier,
  getCvarAllocation,
} = require('./internal/aiGatewayController');

const router = express.Router();

// Every ai-gateway route requires a logged-in user — this is
// dashboard/portfolio-adjacent data, not public.
router.use(requireAuth);

router.get('/market-data/ohlcv/:ticker', getOhlcv);
router.post('/market-data/ohlcv/universe/fetch', fetchOhlcvUniverse);
router.get('/market-data/fundamentals/:ticker', getFundamentals);
router.post('/market-data/fundamentals/universe/fetch', fetchFundamentalsUniverse);
router.get('/news/:ticker', getNews);
router.post('/news/universe/fetch', fetchNewsUniverse);

// Step 5 — Optimization Core (Phase 3). risk_lambda is always
// server-derived from the authenticated user's stored profile, never
// accepted from the request body — see aiGatewayController.js.
router.post('/optimize', getOptimalAllocation);
router.post('/optimize/frontier', getEfficientFrontier);
router.post('/optimize/cvar', getCvarAllocation);

module.exports = { router };