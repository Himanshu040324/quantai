// backend/src/modules/auth/index.js
// NEW FILE
//
// PUBLIC CONTRACT for the auth module.
// Other modules must import ONLY from this file.

const express = require('express');
const { signup, login, refresh, logout } = require('./internal/authController');
const { requireAuth } = require('./internal/authMiddleware');

const router = express.Router();

router.post('/signup', signup);
router.post('/login', login);
router.post('/refresh', refresh);
router.post('/logout', logout);

module.exports = {
  router,
  requireAuth, // exported so other modules can protect their own routes
};