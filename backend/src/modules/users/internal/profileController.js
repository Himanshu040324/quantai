// backend/src/modules/users/internal/profileController.js
// NEW FILE
//
// INTERNAL MODULE FILE — do not import outside modules/users/.
// These handlers always operate on req.user.id (set by
// auth.requireAuth), so a user can only ever read/write their own
// profile through these routes — there's no separate resource id
// to check ownership against, unlike portfolios/index.js's
// getOwnedPortfolioOrThrow pattern.

const { User, RISK_LABELS } = require('./user.model');
const { labelToLambda } = require('./riskMapping');

/**
 * GET /api/users/profile
 * Returns the authenticated user's stored profile.
 */
async function getProfile(req, res) {
  const user = await User.findById(req.user.id);
  if (!user) {
    return res.status(404).json({ errors: ['User not found.'] });
  }
  return res.status(200).json({ user: user.toJSON() });
}

/**
 * PUT /api/users/profile
 * Body: { capital, timeHorizonYears, riskLabel }
 * riskLambda is always derived server-side — never accepted as input.
 */
async function putProfile(req, res) {
  const { capital, timeHorizonYears, riskLabel } = req.body;
  const errors = [];

  if (capital !== undefined && (!Number.isInteger(capital) || capital < 0)) {
    errors.push('capital must be a non-negative integer (smallest currency unit).');
  }
  if (timeHorizonYears !== undefined && (!Number.isInteger(timeHorizonYears) || timeHorizonYears < 1)) {
    errors.push('timeHorizonYears must be a positive whole number.');
  }
  if (riskLabel !== undefined && !RISK_LABELS.includes(riskLabel)) {
    errors.push(`riskLabel must be one of: ${RISK_LABELS.join(', ')}`);
  }
  if (errors.length > 0) {
    return res.status(400).json({ errors });
  }

  const update = {};
  if (capital !== undefined) update.capital = capital;
  if (timeHorizonYears !== undefined) update.timeHorizonYears = timeHorizonYears;
  if (riskLabel !== undefined) {
    update.riskLabel = riskLabel;
    update.riskLambda = labelToLambda(riskLabel);
  }

  const user = await User.findByIdAndUpdate(req.user.id, update, {
    new: true,
    runValidators: true,
  });

  if (!user) {
    return res.status(404).json({ errors: ['User not found.'] });
  }

  return res.status(200).json({ user: user.toJSON() });
}

module.exports = { getProfile, putProfile };