const express = require('express');
const { generateResetToken, hashPassword } = require('../../utils/auth');
const { sendResetEmail } = require('../../services/email-service');
const csrfProtection = require('../../middleware/csrf');
const { db } = require('../../db/database');

const router = express.Router();

/**
 * Request password reset
 * POST /api/auth/reset-password
 */
router.post('/', csrfProtection, (req, res) => {
  try {
    const { email } = req.body;

    if (!email) {
      return res.status(400).json({ error: 'Email is required' });
    }

    // Find user by email
    db.get('SELECT id FROM users WHERE email = ?', [email], (err, user) => {
      if (err) {
        return res.status(500).json({ error: 'Database error' });
      }

      // Always return success to prevent email enumeration
      if (user) {
        // Generate reset token (30-min expiry)
        const { token, expires } = generateResetToken(user.id);

        db.run(
          'INSERT INTO password_reset (user_id, token, expires) VALUES (?, ?, ?)',
          [user.id, token, expires],
          function () {
            // Send reset email
            sendResetEmail(email, token);
          }
        );
      }

      // Return generic response
      res.json({
        message: 'If an account exists with that email, a password reset link has been sent.'
      });
    });

  } catch (error) {
    console.error('Password reset request error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
