// backend/src/modules/users/index.js
// NEW FILE
//
// PUBLIC CONTRACT for the users module.
// Other modules (auth, portfolios, ai-gateway, etc.) must import ONLY
// from this file — never reach into internal/user.model.js directly.
// This is the boundary rule from Master_Prompt.md section 3.

const express = require('express');
const { User, RISK_LABELS } = require('./internal/user.model');
const { labelToLambda, RISK_LAMBDA_MAP } = require('./internal/riskMapping');
const { getProfile, putProfile } = require('./internal/profileController');
// Cross-module import of auth is allowed here because it's the
// public contract (auth/index.js), not an internal file — consistent
// with the boundary rule.
const { requireAuth } = require('../auth');

const router = express.Router();
router.get('/profile', requireAuth, getProfile);
router.put('/profile', requireAuth, putProfile);

/**
 * Create a new user document. Expects passwordHash to already be
 * hashed by the caller (auth module owns hashing, not this module).
 */
async function createUser({ email, passwordHash, capital, timeHorizonYears, riskLabel }) {
  const riskLambda = labelToLambda(riskLabel);
  const user = await User.create({
    email,
    passwordHash,
    capital,
    timeHorizonYears,
    riskLabel,
    riskLambda,
  });
  return user;
}

/**
 * Fetch a user by email WITH the password hash included, for login
 * verification only. Callers must never forward passwordHash onward.
 */
async function findByEmailWithHash(email) {
  return User.findOne({ email: email.toLowerCase().trim() }).select('+passwordHash');
}

async function findById(userId) {
  return User.findById(userId);
}

/**
 * Update the investment profile fields. riskLambda is always
 * recomputed here from riskLabel — never accepted as a raw input,
 * per the anti-hallucination / non-speculative data rule.
 */
async function updateProfile(userId, { capital, timeHorizonYears, riskLabel }) {
  const update = {};
  if (capital !== undefined) update.capital = capital;
  if (timeHorizonYears !== undefined) update.timeHorizonYears = timeHorizonYears;
  if (riskLabel !== undefined) {
    update.riskLabel = riskLabel;
    update.riskLambda = labelToLambda(riskLabel);
  }

  const user = await User.findByIdAndUpdate(userId, update, {
    new: true,
    runValidators: true,
  });
  return user;
}

async function incrementRefreshTokenVersion(userId) {
  return User.findByIdAndUpdate(
    userId,
    { $inc: { refreshTokenVersion: 1 } },
    { new: true }
  );
}

module.exports = {
  router,
  // model export is intentional here so Mongoose can register it and
  // so ownership-check code elsewhere can type against it — but reads
  // and writes should go through the functions above wherever possible.
  User,
  RISK_LABELS,
  RISK_LAMBDA_MAP,
  createUser,
  findByEmailWithHash,
  findById,
  updateProfile,
  incrementRefreshTokenVersion,
};