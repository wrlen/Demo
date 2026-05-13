const express = require('express');
const database = require('../../db/database');
const db = database.db;
const { hashPassword, generateVerificationToken } = require('../../utils/auth');
const { sendVerificationEmail } = require('../../services/email-service');
const csrfProtection = require('../../middleware/csrf');

const router = express.Router();

// Apply CSRF protection to POST requests
router.post('/', csrfProtection, async (req, res) => {
  try {
    const { email, password } = req.body;

    // Validate input
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    // Email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({ error: 'Invalid email format' });
    }

    // Password complexity validation: at least 8 characters with letters and numbers
    if (!/^(?=.*[a-zA-Z])(?=.*\d).{8,}$/.test(password)) {
      return res.status(400).json({
        error: 'Password must be at least 8 characters with letters and numbers'
      });
    }

    // Check if email already exists
    db.get('SELECT id FROM users WHERE email = ?', [email], (err, row) => {
      if (err) {
        console.error('Database error:', err);
        return res.status(500).json({ error: 'Database error' });
      }

      if (row) {
        return res.status(400).json({ error: 'Email already registered' });
      }

      // Hash password and create user
      const passwordHash = hashPassword(password);

      db.run(
        'INSERT INTO users (email, password_hash, is_verified) VALUES (?, ?, ?)',
        [email, passwordHash, 0],
        function (err) {
          if (err) {
            return res.status(500).json({ error: 'Failed to create user' });
          }

          const userId = this.lastID;

          // Generate verification token
          const { token, expires } = generateVerificationToken(userId);

          db.run(
            'INSERT INTO verification (user_id, token, expires) VALUES (?, ?, ?)',
            [userId, token, expires],
            function (err) {
              if (err) {
                return res.status(500).json({ error: 'Failed to store verification token' });
              }

              // Send verification email
              sendVerificationEmail(email, token);

              res.status(201).json({
                message: 'Registration successful. Please check your email to verify your account.',
                user: {
                  id: userId,
                  email,
                  isVerified: false
                }
              });
            }
          );
        }
      );
    });

  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
