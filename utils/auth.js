const bcrypt = require('bcrypt');
const crypto = require('crypto');

/**
 * Hash a password using bcrypt
 * @param {string} password - Plain text password
 * @returns {string} - bcrypt hash
 */
const hashPassword = (password) => {
  return bcrypt.hashSync(password, 10);
};

/**
 * Verify a password against a stored hash
 * @param {string} password - Plain text password
 * @param {string} hash - Stored bcrypt hash
 * @returns {boolean} - Whether password matches
 */
const verifyPassword = (password, hash) => {
  return bcrypt.compareSync(password, hash);
};

/**
 * Generate a verification token (30-minute expiry)
 * @param {number} userId - User ID to generate token for
 * @returns {{ token: string, expires: number }} - Token and expiry timestamp (ms)
 */
const generateVerificationToken = (userId) => {
  const token = crypto.randomBytes(32).toString('hex');
  const expires = Date.now() + 30 * 60 * 1000; // 30 minutes in ms
  return { token, expires, userId };
};

/**
 * Generate a password reset token (30-min expiry)
 * @param {number} userId - User ID to generate token for
 * @returns {{ token: string, expires: number }} - Token and expiry timestamp (ms)
 */
const generateResetToken = (userId) => {
  const token = crypto.randomBytes(32).toString('hex');
  const expires = Date.now() + 30 * 60 * 1000; // 30 minutes in ms
  return { token, expires, userId };
};

module.exports = {
  hashPassword,
  verifyPassword,
  generateVerificationToken,
  generateResetToken
};
