// backend/src/modules/auth/internal/authController.js
// NEW FILE
//
// INTERNAL MODULE FILE — do not import outside modules/auth/.
// Consumes the users module ONLY via its public contract
// (require('../../users')), never via users/internal/*, per the
// module boundary rule.

const bcrypt = require('bcrypt');
// NOTE: users module is required lazily inside each handler below,
// not at top-level. auth/index.js and users/index.js reference each
// other (users needs auth.requireAuth for its profile routes; auth
// needs users' data functions here), which creates a circular
// require. Node handles circular requires by returning a partially
// populated module.exports for whichever side loads second — at
// top-level that can arrive as `undefined` depending on load order.
// Requiring inside the function body defers resolution until after
// both modules have finished their initial load, which is the
// standard safe pattern for this situation.
const { validateSignupInput, validateLoginInput } = require('./validators');
const {
  signAccessToken,
  signRefreshToken,
  verifyRefreshToken,
} = require('./tokens');
const env = require('../../../shared/env');

const BCRYPT_COST_FACTOR = 12;

const REFRESH_COOKIE_NAME = 'refreshToken';
const REFRESH_COOKIE_OPTIONS = {
  httpOnly: true,
  secure: env.NODE_ENV === 'production', // requires HTTPS in prod
  sameSite: 'lax',
  maxAge: env.REFRESH_TOKEN_TTL_MS,
  path: '/api/auth', // scope the cookie to auth routes only
};

function setRefreshCookie(res, token) {
  res.cookie(REFRESH_COOKIE_NAME, token, REFRESH_COOKIE_OPTIONS);
}

function clearRefreshCookie(res) {
  res.clearCookie(REFRESH_COOKIE_NAME, { path: REFRESH_COOKIE_OPTIONS.path });
}

/**
 * POST /api/auth/signup
 * Body: { email, password, capital, timeHorizonYears, riskLabel }
 *
 * Note: capital/timeHorizonYears/riskLabel are accepted here so a user
 * can complete the investment profile form as part of signup (per the
 * Phase 1 deliverable). If you'd rather split signup and profile into
 * two separate steps, defer these to the profile endpoint instead —
 * both are wired through usersModule.createUser either way.
 */
async function signup(req, res) {
  const usersModule = require('../../users');
  const { email, password, capital, timeHorizonYears, riskLabel } = req.body;

  const errors = validateSignupInput({ email, password });
  if (!Number.isInteger(capital) || capital < 0) {
    errors.push('capital is required and must be an integer (smallest currency unit).');
  }
  if (!Number.isInteger(timeHorizonYears) || timeHorizonYears < 1) {
    errors.push('timeHorizonYears is required and must be a positive whole number.');
  }
  if (!usersModule.RISK_LABELS.includes(riskLabel)) {
    errors.push(`riskLabel must be one of: ${usersModule.RISK_LABELS.join(', ')}`);
  }
  if (errors.length > 0) {
    return res.status(400).json({ errors });
  }

  const existing = await usersModule.findByEmailWithHash(email);
  if (existing) {
    // Deliberately vague message — don't confirm which field was wrong.
    return res.status(409).json({ errors: ['An account with that email already exists.'] });
  }

  const passwordHash = await bcrypt.hash(password, BCRYPT_COST_FACTOR);

  const user = await usersModule.createUser({
    email: email.toLowerCase().trim(),
    passwordHash,
    capital,
    timeHorizonYears,
    riskLabel,
  });

  const accessToken = signAccessToken(user);
  const refreshToken = signRefreshToken(user);
  setRefreshCookie(res, refreshToken);

  return res.status(201).json({
    user: user.toJSON(),
    accessToken,
  });
}

/**
 * POST /api/auth/login
 * Body: { email, password }
 */
async function login(req, res) {
  const usersModule = require('../../users');
  const { email, password } = req.body;

  const errors = validateLoginInput({ email, password });
  if (errors.length > 0) {
    return res.status(400).json({ errors });
  }

  const user = await usersModule.findByEmailWithHash(email);
  // Same generic error whether the email doesn't exist or the password
  // is wrong — never reveal which one it was.
  const genericError = { errors: ['Invalid email or password.'] };

  if (!user) {
    return res.status(401).json(genericError);
  }

  const passwordMatches = await bcrypt.compare(password, user.passwordHash);
  if (!passwordMatches) {
    return res.status(401).json(genericError);
  }

  const accessToken = signAccessToken(user);
  const refreshToken = signRefreshToken(user);
  setRefreshCookie(res, refreshToken);

  return res.status(200).json({
    user: user.toJSON(),
    accessToken,
  });
}

/**
 * POST /api/auth/refresh
 * Reads the httpOnly refresh cookie, issues a new access token.
 * Rejects if the token's version doesn't match the user's current
 * refreshTokenVersion (i.e. it was invalidated by a logout-everywhere
 * or password change).
 */
async function refresh(req, res) {
  const usersModule = require('../../users');
  const token = req.cookies?.[REFRESH_COOKIE_NAME];
  if (!token) {
    return res.status(401).json({ errors: ['No refresh token provided.'] });
  }

  let payload;
  try {
    payload = verifyRefreshToken(token);
  } catch {
    clearRefreshCookie(res);
    return res.status(401).json({ errors: ['Invalid or expired refresh token.'] });
  }

  const user = await usersModule.findById(payload.sub);
  if (!user || user.refreshTokenVersion !== payload.ver) {
    clearRefreshCookie(res);
    return res.status(401).json({ errors: ['Refresh token has been revoked.'] });
  }

  const accessToken = signAccessToken(user);
  return res.status(200).json({ accessToken });
}

/**
 * POST /api/auth/logout
 * Clears the refresh cookie. Does NOT bump refreshTokenVersion —
 * that's reserved for an explicit "log out everywhere" action, so a
 * single logout doesn't kill sessions on other devices.
 */
async function logout(req, res) {
  clearRefreshCookie(res);
  return res.status(204).send();
}

module.exports = { signup, login, refresh, logout };