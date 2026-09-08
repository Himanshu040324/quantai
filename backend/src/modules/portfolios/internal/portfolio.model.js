// backend/src/modules/portfolios/internal/portfolio.model.js
// NEW FILE
//
// INTERNAL MODULE FILE — do not import this directly from outside
// backend/src/modules/portfolios/. Consume the portfolios module's
// public contract via ../index.js instead.

const mongoose = require('mongoose');

// A single position within a portfolio. Quantities/weights only —
// no price data is cached here; that lives in Phase 2's data pipeline.
const holdingSchema = new mongoose.Schema(
  {
    ticker: {
      type: String,
      required: true,
      trim: true,
      uppercase: true,
    },
    // Allocation weight as a fraction of the portfolio, e.g. 0.22 = 22%.
    // Stored as a plain Number (not currency), so the money-integer
    // rule does not apply to this field — it's a ratio, not an amount.
    weight: {
      type: Number,
      required: true,
      min: 0,
      max: 1,
    },
    // Optional: quantity held, if/when the platform tracks actual
    // share counts rather than target weights only.
    quantity: {
      type: Number,
      min: 0,
    },
  },
  { _id: false }
);

const portfolioSchema = new mongoose.Schema(
  {
    ownerId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true,
    },

    // Human-facing name for this portfolio, in case a user has more
    // than one (e.g. "Retirement", "Aggressive Growth").
    name: {
      type: String,
      required: true,
      trim: true,
      default: 'My Portfolio',
    },

    holdings: {
      type: [holdingSchema],
      default: [],
      validate: {
        validator(holdings) {
          if (holdings.length === 0) return true;
          const total = holdings.reduce((sum, h) => sum + h.weight, 0);
          // Allow small floating-point slack; strict 100% check belongs
          // in the Phase 3 optimizer's validation, not here.
          return Math.abs(total - 1) < 1e-6;
        },
        message: 'holdings weights must sum to 1 (100%)',
      },
    },

    // Snapshot of the most recent optimizer output, so the dashboard
    // can render without re-calling FastAPI on every page load.
    // This is a cache/denormalization, not the source of truth for
    // "what should the allocation be" — that's recomputed in Phase 3+.
    allocationSnapshot: {
      generatedAt: { type: Date },
      method: { type: String, enum: ['markowitz', 'cvar', 'black-litterman', null], default: null },
      expectedReturn: { type: Number },
      expectedVolatility: { type: Number },
    },
  },
  {
    timestamps: true, // createdAt, updatedAt
  }
);

const Portfolio = mongoose.model('Portfolio', portfolioSchema);

module.exports = { Portfolio };