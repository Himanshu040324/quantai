// backend/src/modules/ai-gateway/internal/aiServiceClient.js
// REPLACING EXISTING FILE
//
// The ONLY file that talks to ai-service over HTTP. Controllers call
// proxyRequest() and forward whatever it returns — this file has no
// knowledge of Express req/res, and ai-gatewayController.js has no
// knowledge of URLs or fetch. Keeps the "proxy only, no reshaping"
// rule enforceable: if reshaping ever creeps in, it'll be obvious
// which file it snuck into.
//
// Step 5 addition: optional JSON `body` support, needed for the
// optimize endpoints (POST /optimize, /optimize/frontier, /optimize/cvar)
// which all require a request body — GET-only proxying (Phase 2's
// market-data/news routes) is unaffected.

const env = require('../../../shared/env');

const DEFAULT_TIMEOUT_MS = 15000;

class AiServiceUnavailableError extends Error {
  constructor(message) {
    super(message);
    this.name = 'AiServiceUnavailableError';
    this.status = 502;
  }
}

function buildUrl(path, query) {
  const url = new URL(path, env.FASTAPI_BASE_URL);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, value);
      }
    }
  }
  return url;
}

/**
 * Proxies a single request to ai-service. Returns { status, body }
 * from FastAPI as-is — callers pass this straight through to the
 * client, they don't inspect or transform it.
 *
 * `body`, when provided, is JSON-serialized and sent with a
 * Content-Type: application/json header. Omit for GET requests.
 */
async function proxyRequest(
  method,
  path,
  { query, body, timeoutMs = DEFAULT_TIMEOUT_MS } = {}
) {
  const url = buildUrl(path, query);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  const fetchOptions = { method, signal: controller.signal };
  if (body !== undefined) {
    fetchOptions.headers = { 'Content-Type': 'application/json' };
    fetchOptions.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(url, fetchOptions);
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new AiServiceUnavailableError(`ai-service timed out after ${timeoutMs}ms`);
    }
    throw new AiServiceUnavailableError(`ai-service unreachable: ${err.message}`);
  } finally {
    clearTimeout(timeout);
  }

  let responseBody;
  try {
    responseBody = await response.json();
  } catch {
    throw new AiServiceUnavailableError('ai-service returned a non-JSON response');
  }

  return { status: response.status, body: responseBody };
}

module.exports = { proxyRequest, AiServiceUnavailableError };