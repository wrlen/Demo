const express = require('express');
const { hashPassword } = require('../../utils/auth');
const csrfProtection = require('../../middleware/csrf');
const { db } = require('../../db/database');

const router = express.Router();

/**
 * Confirm password reset with token
 * POST /api/auth/reset/confirm?token={token}
 */
router.post('/', csrfProtection, (req, res) => {
  try {
    const { token, newPassword } = req.query;

    if (!token || !newPassword) {
      return res.status(400).json({ error: 'Token and new password are required' });
    }

    // Validate new password
    if (!/^(?=.*[a-zA-Z])(?=.*\d).{8,}$/.test(newPassword)) {
      return res.status(400).json({
        error: 'Password must be at least 8 characters with letters and numbers'
      });
    }

    // Find valid reset token
    db.get(
      'SELECT * FROM password_reset WHERE token = ?',
      [token],
      (err, row) => {
        if (err) {
          return res.status(500).json({ error: 'Database error' });
        }

        if (!row) {
          return res.status(400).json({ error: 'Invalid reset token' });
        }

        // Check if token has expired
        if (row.expires < Date.now()) {
          return res.status(400).json({ error: 'Reset token has expired. Please request a new one.' });
        }

        // Hash new password and update user
        const newHash = hashPassword(newPassword);

        db.run(
          'UPDATE users SET password_hash = ? WHERE id = ?',
          [newHash, row.user_id],
          function (err) {
            if (err) {
              return res.status(500).json({ error: 'Failed to reset password' });
            }

            // Clean up reset token
            db.run('DELETE FROM password_reset WHERE token = ?', [token]);

            res.json({
              message: 'Password reset successfully! You can now log in with your new password.'
            });
          }
        );
      }
    );

  } catch (error) {
    console.error('Password reset confirmation error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
