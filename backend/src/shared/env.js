// backend/src/shared/env.js
// NEW FILE
//
// Centralized, validated environment access. Import from here instead
// of calling process.env directly, so a missing required var fails
// fast at boot rather than surfacing as a confusing runtime error.

require('dotenv').config();

function required(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

const env = {
  NODE_ENV: process.env.NODE_ENV || 'development',
  PORT: process.env.PORT || 5000,

  MONGODB_URI: required('MONGODB_URI'),

  JWT_ACCESS_SECRET: required('JWT_ACCESS_SECRET'),
  JWT_REFRESH_SECRET: required('JWT_REFRESH_SECRET'),

  ACCESS_TOKEN_TTL: '1h',
  REFRESH_TOKEN_TTL: '30d',
  REFRESH_TOKEN_TTL_MS: 30 * 24 * 60 * 60 * 1000, // 30 days, for cookie maxAge

  CORS_ORIGIN: process.env.CORS_ORIGIN || 'http://localhost:5173',
};

module.exports = env;