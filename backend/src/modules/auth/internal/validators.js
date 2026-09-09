// backend/src/modules/auth/internal/validators.js
// NEW FILE
//
// INTERNAL MODULE FILE — do not import outside modules/auth/.
// Server-side validation per the non-negotiable rule: never trust
// client-side validation alone.

const EMAIL_RE = /^\S+@\S+\.\S+$/;
// Minimum bar: 8+ chars, at least one letter and one number.
// Deliberately not over-engineering password rules here — see Phase 1
// "Common Pitfall" in the plan: don't let auth polish expand scope.
const PASSWORD_RE = /^(?=.*[A-Za-z])(?=.*\d).{8,}$/;

function validateSignupInput({ email, password }) {
  const errors = [];

  if (typeof email !== 'string' || !EMAIL_RE.test(email.trim())) {
    errors.push('A valid email is required.');
  }

  if (typeof password !== 'string' || !PASSWORD_RE.test(password)) {
    errors.push('Password must be at least 8 characters and include a letter and a number.');
  }

  return errors;
}

function validateLoginInput({ email, password }) {
  const errors = [];
  if (typeof email !== 'string' || !email.trim()) {
    errors.push('Email is required.');
  }
  if (typeof password !== 'string' || !password) {
    errors.push('Password is required.');
  }
  return errors;
}

module.exports = { validateSignupInput, validateLoginInput };