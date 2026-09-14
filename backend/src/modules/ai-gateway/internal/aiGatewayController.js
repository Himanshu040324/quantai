// backend/src/modules/ai-gateway/internal/aiGatewayController.js
// NEW FILE
//
// Thin handlers only — each one forwards the request to ai-service
// and relays the response verbatim. No business logic, no MongoDB
// access, no reshaping of FastAPI's payload. If a handler here starts
// doing more than "pick a path, forward query params, relay result",
// that logic belongs in ai-service instead.

const { proxyRequest } = require('./aiServiceClient');

function relay(res, { status, body }) {
  res.status(status).json(body);
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

module.exports = {
  getOhlcv,
  fetchOhlcvUniverse,
  getFundamentals,
  fetchFundamentalsUniverse,
  getNews,
  fetchNewsUniverse,
};