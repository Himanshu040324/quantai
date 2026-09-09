// backend/src/modules/auth/internal/authMiddleware.js
// NEW FILE
//
// INTERNAL MODULE FILE — do not import outside modules/auth/.
// Note: authenticating the request is necessary but NOT sufficient
// for resource access. Ownership checks (e.g.
// portfolios.getOwnedPortfolioOrThrow) must still be applied in the
// route/service layer for any resource-scoped endpoint.

const { verifyAccessToken } = require('./tokens');

function requireAuth(req, res, next) {
  const authHeader = req.headers.authorization || '';
  const [scheme, token] = authHeader.split(' ');

  if (scheme !== 'Bearer' || !token) {
    return res.status(401).json({ errors: ['Missing or malformed Authorization header.'] });
  }

  try {
    const payload = verifyAccessToken(token);
    // Only the user id is attached here — full user document is
    // fetched by handlers that actually need it, to avoid an extra
    // DB round trip on every single request.
    req.user = { id: payload.sub };
    return next();
  } catch {
    return res.status(401).json({ errors: ['Invalid or expired access token.'] });
  }
}

module.exports = { requireAuth };