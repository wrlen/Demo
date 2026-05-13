const express = require('express');
const router = express.Router();
const { db } = require('../../db/database');

/**
 * Verify email using token from query parameter
 * GET /api/auth/verify?token={token}
 */
router.get('/', (req, res) => {
  const { token } = req.query;

  if (!token) {
    return res.status(400).json({ error: 'Verification token is required' });
  }

  // Find verification token
  db.get(
    'SELECT * FROM verification WHERE token = ?',
    [token],
    (err, row) => {
      if (err) {
        return res.status(500).json({ error: 'Database error' });
      }

      if (!row) {
        return res.status(400).json({ error: 'Invalid verification token' });
      }

      // Check if token has expired
      if (row.expires < Date.now()) {
        // Clean up expired token
        db.run('DELETE FROM verification WHERE token = ?', [token]);
        return res.status(400).json({ error: 'Verification token has expired' });
      }

      // Activate user account
      db.run(
        'UPDATE users SET is_verified = 1 WHERE id = ?',
        [row.user_id],
        function (err) {
          if (err) {
            return res.status(500).json({ error: 'Failed to verify account' });
          }

          // Clean up verification token
          db.run('DELETE FROM verification WHERE token = ?', [token]);

          res.json({
            message: 'Email verified successfully! You can now log in.',
            verified: true
          });
        }
      );
    }
  );
});

module.exports = router;
