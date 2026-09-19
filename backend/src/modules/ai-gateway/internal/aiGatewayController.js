// backend/src/modules/ai-gateway/internal/aiGatewayController.js
// REPLACING EXISTING FILE
//
// Thin handlers only — each one forwards the request to ai-service
// and relays the response verbatim. No business logic, no MongoDB
// access beyond the one explicit exception below, no reshaping of
// FastAPI's payload.
//
// Step 5 addition: the three optimize handlers (getOptimalAllocation,
// getEfficientFrontier, getCvarAllocation) each need risk_lambda,
// which is never sent by the client and never trusted from the
// client if it were — it's the server-derived value from Phase 1's
// riskMapping, stored on the user's own document. requireAuth only
// attaches { id } to req.user (see authMiddleware.js), so each
// handler does its own users.findById lookup via users' public
// contract (never users/internal/ directly) to read riskLambda.
// This is a deliberate, minimal exception to "no business logic in
// controllers" — it's an ownership-scoped read of the requesting
// user's own stored value, not new business logic.

const { proxyRequest } = require('./aiServiceClient');
const { findById } = require('../../users');

function relay(res, { status, body }) {
  res.status(status).json(body);
}

async function getRiskLambdaForRequest(req) {
  const user = await findById(req.user.id);
  if (!user) {
    // Shouldn't happen for a valid access token, but fail loudly
    // rather than silently forwarding an undefined risk_lambda.
    const err = new Error('Authenticated user not found.');
    err.status = 401;
    throw err;
  }
  return user.riskLambda;
}

async function getOhlcv(req, res, next) {
  try {
    const { ticker } = req.params;
    const result = await proxyRequest('GET', `/market-data/ohlcv/${encodeURIComponent(ticker)}`, {
      query: { years: req.query.years },
    });
    relay(res, result);
  } catch (err) {
    next(err);
  }
}

async function fetchOhlcvUniverse(req, res, next) {
  try {
    const result = await proxyRequest('POST', '/market-data/ohlcv/universe/fetch', {
      query: { years: req.query.years },
      timeoutMs: 60000, // universe backfill is slow by design (Step 2/3) — give it room
    });
    relay(res, result);
  } catch (err) {
    next(err);
  }
}

async function getFundamentals(req, res, next) {
  try {
    const { ticker } = req.params;
    const result = await proxyRequest(
      'GET',
      `/market-data/fundamentals/${encodeURIComponent(ticker)}`,
    );
    relay(res, result);
  } catch (err) {
    next(err);
  }
}

async function fetchFundamentalsUniverse(req, res, next) {
  try {
    const result = await proxyRequest('POST', '/market-data/fundamentals/universe/fetch', {
      timeoutMs: 60000,
    });
    relay(res, result);
  } catch (err) {
    next(err);
  }
}

async function getNews(req, res, next) {
  try {
    const { ticker } = req.params;
    const result = await proxyRequest('GET', `/news/${encodeURIComponent(ticker)}`);
    relay(res, result);
  } catch (err) {
    next(err);
  }
}

async function fetchNewsUniverse(req, res, next) {
  try {
    const result = await proxyRequest('POST', '/news/universe/fetch', { timeoutMs: 60000 });
    relay(res, result);
  } catch (err) {
    next(err);
  }
}

async function getOptimalAllocation(req, res, next) {
  try {
    const riskLambda = await getRiskLambdaForRequest(req);
    const result = await proxyRequest('POST', '/optimize', {
      body: { risk_lambda: riskLambda, years: req.body.years },
    });
    relay(res, result);
  } catch (err) {
    next(err);
  }
}

async function getEfficientFrontier(req, res, next) {
  try {
    const riskLambda = await getRiskLambdaForRequest(req);
    const result = await proxyRequest('POST', '/optimize/frontier', {
      body: {
        risk_lambda: riskLambda,
        years: req.body.years,
        num_points: req.body.num_points,
      },
    });
    relay(res, result);
  } catch (err) {
    next(err);
  }
}

async function getCvarAllocation(req, res, next) {
  try {
    const riskLambda = await getRiskLambdaForRequest(req);
    const result = await proxyRequest('POST', '/optimize/cvar', {
      body: { risk_lambda: riskLambda, years: req.body.years },
    });
    relay(res, result);
  } catch (err) {
    next(err);
  }
}

module.exports = {
  getOhlcv,
  fetchOhlcvUniverse,
  getFundamentals,
  fetchFundamentalsUniverse,
  getNews,
  fetchNewsUniverse,
  getOptimalAllocation,
  getEfficientFrontier,
  getCvarAllocation,
};