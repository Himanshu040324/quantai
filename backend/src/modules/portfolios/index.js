// backend/src/modules/portfolios/index.js
// NEW FILE
//
// PUBLIC CONTRACT for the portfolios module.
// Other modules must import ONLY from this file — never reach into
// internal/portfolio.model.js directly. Boundary rule per
// Master_Prompt.md section 3.

const { Portfolio } = require('./internal/portfolio.model');

async function createPortfolio(ownerId, { name, holdings } = {}) {
  return Portfolio.create({ ownerId, name, holdings });
}

async function findById(portfolioId) {
  return Portfolio.findById(portfolioId);
}

async function findAllForOwner(ownerId) {
  return Portfolio.find({ ownerId });
}

/**
 * Explicit ownership check, per the non-negotiable rule:
 * "Authentication is necessary but never sufficient."
 * Call this in the service/business logic layer before any read or
 * write on a specific portfolio, in addition to requiring a valid JWT.
 *
 * @returns {Promise<Object>} the portfolio document if owned by userId
 * @throws {Error} 'NOT_FOUND' or 'FORBIDDEN' — map these to 404/403 in
 *   the route handler; never leak "exists but not yours" vs "doesn't
 *   exist" distinctions to the client either way.
 */
async function getOwnedPortfolioOrThrow(portfolioId, userId) {
  const portfolio = await Portfolio.findById(portfolioId);
  if (!portfolio) {
    const err = new Error('NOT_FOUND');
    err.status = 404;
    throw err;
  }
  if (portfolio.ownerId.toString() !== userId.toString()) {
    const err = new Error('FORBIDDEN');
    err.status = 404; // 404, not 403 — avoid confirming resource existence to non-owners
    throw err;
  }
  return portfolio;
}

async function updateAllocationSnapshot(portfolioId, snapshot) {
  return Portfolio.findByIdAndUpdate(
    portfolioId,
    {
      allocationSnapshot: {
        ...snapshot,
        generatedAt: new Date(),
      },
    },
    { new: true, runValidators: true }
  );
}

module.exports = {
  Portfolio,
  createPortfolio,
  findById,
  findAllForOwner,
  getOwnedPortfolioOrThrow,
  updateAllocationSnapshot,
};