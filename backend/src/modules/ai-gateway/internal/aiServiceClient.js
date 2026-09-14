// backend/src/modules/ai-gateway/internal/aiServiceClient.js
// NEW FILE
//
// The ONLY file that talks to ai-service over HTTP. Controllers call
// proxyRequest() and forward whatever it returns — this file has no
// knowledge of Express req/res, and ai-gatewayController.js has no
// knowledge of URLs or fetch. Keeps the "proxy only, no reshaping"
// rule enforceable: if reshaping ever creeps in, it'll be obvious
// which file it snuck into.

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
 */
async function proxyRequest(method, path, { query, timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
  const url = buildUrl(path, query);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  let response;
  try {
    response = await fetch(url, { method, signal: controller.signal });
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new AiServiceUnavailableError(`ai-service timed out after ${timeoutMs}ms`);
    }
    throw new AiServiceUnavailableError(`ai-service unreachable: ${err.message}`);
  } finally {
    clearTimeout(timeout);
  }

  let body;
  try {
    body = await response.json();
  } catch {
    throw new AiServiceUnavailableError('ai-service returned a non-JSON response');
  }

  return { status: response.status, body };
}

module.exports = { proxyRequest, AiServiceUnavailableError };