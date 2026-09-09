// backend/src/modules/auth/internal/tokens.js
// NEW FILE
//
// INTERNAL MODULE FILE — do not import outside modules/auth/.

const jwt = require('jsonwebtoken');
const env = require('../../../shared/env');

/**
 * Access token: short-lived, sent in the JSON response body, held in
 * memory on the client (never localStorage). Used to authorize API
 * requests via the Authorization header.
 */
function signAccessToken(user) {
  return jwt.sign(
    { sub: user._id.toString(), type: 'access' },
    env.JWT_ACCESS_SECRET,
    { expiresIn: env.ACCESS_TOKEN_TTL }
  );
}

/**
 * Refresh token: long-lived, sent ONLY via httpOnly cookie, never
 * exposed to client-side JS. Includes refreshTokenVersion so it can
 * be invalidated server-side (logout-everywhere, password change)
 * without needing a token blocklist.
 */
function signRefreshToken(user) {
  return jwt.sign(
    {
      sub: user._id.toString(),
      type: 'refresh',
      ver: user.refreshTokenVersion,
    },
    env.JWT_REFRESH_SECRET,
    { expiresIn: env.REFRESH_TOKEN_TTL }
  );
}

function verifyAccessToken(token) {
  const payload = jwt.verify(token, env.JWT_ACCESS_SECRET);
  if (payload.type !== 'access') {
    throw new Error('Invalid token type');
  }
  return payload;
}

function verifyRefreshToken(token) {
  const payload = jwt.verify(token, env.JWT_REFRESH_SECRET);
  if (payload.type !== 'refresh') {
    throw new Error('Invalid token type');
  }
  return payload;
}

module.exports = {
  signAccessToken,
  signRefreshToken,
  verifyAccessToken,
  verifyRefreshToken,
};