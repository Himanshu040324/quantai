// backend/src/modules/users/internal/riskMapping.js
// NEW FILE
//
// INTERNAL MODULE FILE. Single source of truth for label -> lambda.
// Phase 3's optimizer ultimately consumes riskLambda as stored on the
// User document — this function is only ever called server-side when
// writing that field, never trusted from client input.

const RISK_LAMBDA_MAP = Object.freeze({
  conservative: 4.0,
  moderate: 2.5,
  aggressive: 1.2,
});
// Lower lambda = less risk-averse = optimizer tolerates more variance
// for higher expected return. Tune these three constants in one place
// only; nothing else should hardcode a lambda value.

/**
 * @param {string} riskLabel - one of 'conservative' | 'moderate' | 'aggressive'
 * @returns {number} riskLambda
 * @throws {Error} if riskLabel is not a recognized value
 */
function labelToLambda(riskLabel) {
  const lambda = RISK_LAMBDA_MAP[riskLabel];
  if (lambda === undefined) {
    throw new Error(`Unknown riskLabel: "${riskLabel}"`);
  }
  return lambda;
}

module.exports = { labelToLambda, RISK_LAMBDA_MAP };