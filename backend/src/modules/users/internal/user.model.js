// backend/src/modules/users/internal/user.model.js
// NEW FILE
//
// INTERNAL MODULE FILE — do not import this directly from outside
// backend/src/modules/users/. Consume the users module's public
// contract via ../index.js instead.

const mongoose = require('mongoose');

const RISK_LABELS = ['conservative', 'moderate', 'aggressive'];

const userSchema = new mongoose.Schema(
  {
    email: {
      type: String,
      required: true,
      unique: true,
      lowercase: true,
      trim: true,
      // Basic shape check server-side; full validation happens in the
      // auth module's request validators, not here.
      match: [/^\S+@\S+\.\S+$/, 'Invalid email format'],
      index: true,
    },

    // Never store plaintext passwords. bcrypt hash only.
    passwordHash: {
      type: String,
      required: true,
      select: false, // excluded from queries by default; opt in explicitly
    },

    // --- Investment profile fields ---
    // Stored as an integer in the smallest currency unit (e.g. paise for
    // INR, cents for USD) per the project's monetary integrity rule.
    // Never store this as a float or as major units.
    capital: {
      type: Number,
      required: true,
      min: 0,
      validate: {
        validator: Number.isInteger,
        message: 'capital must be an integer in the smallest currency unit (e.g. paise/cents)',
      },
    },

    timeHorizonYears: {
      type: Number,
      required: true,
      min: 1,
      max: 50,
      validate: {
        validator: Number.isInteger,
        message: 'timeHorizonYears must be a whole number of years',
      },
    },

    // Human-facing label, chosen by the user in the profile form.
    riskLabel: {
      type: String,
      required: true,
      enum: {
        values: RISK_LABELS,
        message: 'riskLabel must be one of: conservative, moderate, aggressive',
      },
    },

    // Numeric risk-aversion parameter (λ) derived server-side from
    // riskLabel via modules/users/internal/riskMapping.js.
    // This is the value Phase 3's optimizer consumes directly — never
    // accept this from the client, always compute it.
    riskLambda: {
      type: Number,
      required: true,
      min: 0,
    },

    refreshTokenVersion: {
      // Incremented to invalidate all outstanding refresh tokens
      // (e.g. on logout-everywhere or password change).
      type: Number,
      default: 0,
    },
  },
  {
    timestamps: true, // createdAt, updatedAt
  }
);

// Never leak the hash even if someone forgets `select: false` handling
// on a specific query (e.g. .lean() results, toJSON in API responses).
userSchema.set('toJSON', {
  transform: (_doc, ret) => {
    delete ret.passwordHash;
    delete ret.__v;
    return ret;
  },
});

const User = mongoose.model('User', userSchema);

module.exports = { User, RISK_LABELS };