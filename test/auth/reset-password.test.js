const request = require('supertest');
const { app, db, _clear } = require('../../server');

describe('Authentication Password Reset Tests', () => {
  beforeEach(() => {
    _clear();
  });

  describe('POST /api/auth/reset-password', () => {
    test('should send reset email for registered user', async () => {
      // First register a user
      await request(app).post('/api/auth/register').send({
        email: 'reset@test.com',
        password: 'password123'
      });

      const response = await request(app)
        .post('/api/auth/reset-password')
        .send({ email: 'reset@test.com' });

      expect(response.status).toBe(200);
      expect(response.body.message).toContain('password reset link');
    });

    test('should return success even for non-existent email', async () => {
      const response = await request(app)
        .post('/api/auth/reset-password')
        .send({ email: 'nonexistent@test.com' });

      expect(response.status).toBe(200);
      expect(response.body.message).toContain('password reset link');
    });

    test('should reject missing email', async () => {
      const response = await request(app)
        .post('/api/auth/reset-password')
        .send({});

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('Email is required');
    });
  });

  describe('POST /api/auth/reset/confirm', () => {
    test('should confirm password reset with valid token', async () => {
      // Register a user
      await request(app).post('/api/auth/register').send({
        email: 'newpass@test.com',
        password: 'oldpassword123'
      });

      // Get user ID
      const user = await new Promise((resolve, reject) => {
        db.get('SELECT id FROM users WHERE email = ?', ['newpass@test.com'], (err, row) => {
          err ? reject(err) : resolve(row);
        });
      });

      // Create reset token
      const resetToken = 'reset-token-12345';
      const expires = Date.now() + 30 * 60 * 1000;

      await new Promise((resolve, reject) => {
        db.run(
          'INSERT INTO password_reset (user_id, token, expires) VALUES (?, ?, ?)',
          [user.id, resetToken, expires],
          function(err) { err ? reject(err) : resolve(); }
        );
      });

      const response = await request(app)
        .post('/api/auth/reset/confirm')
        .query({
          token: resetToken,
          newPassword: 'newpassword456'
        });

      expect(response.status).toBe(200);
      expect(response.body.message).toContain('Password reset successfully');

      // Verify old password no longer works
      const invalidResponse = await request(app)
        .post('/api/auth/login')
        .send({
          email: 'newpass@test.com',
          password: 'oldpassword123'
        });
      expect(invalidResponse.status).toBe(401);

      // Verify new password works
      const validResponse = await request(app)
        .post('/api/auth/login')
        .send({
          email: 'newpass@test.com',
          password: 'newpassword456'
        });
      expect(validResponse.status).toBe(200);
    });

    test('should reject invalid token', async () => {
      const response = await request(app)
        .post('/api/auth/reset/confirm')
        .query({
          token: 'invalid-token',
          newPassword: 'newpassword123'
        });

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('Invalid reset token');
    });

    test('should reject expired token', async () => {
      // Get user ID
      const user = await new Promise((resolve, reject) => {
        db.get('SELECT id FROM users WHERE email = ?', ['reset@test.com'], (err, row) => {
          if (err || !row) {
            // Create user first
            db.run(
              'INSERT INTO users (email, password_hash, is_verified) VALUES (?, ?, ?)',
              ['reset@test.com', '$2b$10$TestHash', 0],
              function() {
                db.get('SELECT id FROM users WHERE email = ?', ['reset@test.com'], (err, row) => {
                  resolve(row);
                });
              }
            );
          } else {
            resolve(row);
          }
        });
      });

      // Create expired token
      const expiredToken = 'expired-reset-token';
      const pastTime = Date.now() - 1000 * 60 * 5; // 5 minutes ago

      await new Promise((resolve, reject) => {
        db.run(
          'INSERT INTO password_reset (user_id, token, expires) VALUES (?, ?, ?)',
          [user.id, expiredToken, pastTime],
          function(err) { err ? reject(err) : resolve(); }
        );
      });

      const response = await request(app)
        .post('/api/auth/reset/confirm')
        .query({
          token: expiredToken,
          newPassword: 'newpassword123'
        });

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('Reset token has expired. Please request a new one.');
    });

    test('should reject weak new password', async () => {
      // Register a user and create reset token
      await request(app).post('/api/auth/register').send({
        email: 'weaknew@test.com',
        password: 'oldpass123'
      });

      const user = await new Promise((resolve, reject) => {
        db.get('SELECT id FROM users WHERE email = ?', ['weaknew@test.com'], (err, row) => {
          err ? reject(err) : resolve(row);
        });
      });

      const token = 'test-token-reset';
      const expires = Date.now() + 30 * 60 * 1000;

      await new Promise((resolve, reject) => {
        db.run(
          'INSERT INTO password_reset (user_id, token, expires) VALUES (?, ?, ?)',
          [user.id, token, expires],
          function(err) { err ? reject(err) : resolve(); }
        );
      });

      const response = await request(app)
        .post('/api/auth/reset/confirm')
        .query({
          token: token,
          newPassword: 'weakpassword' // Only letters, no numbers
        });

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('Password must be at least 8 characters with letters and numbers');
    });

    test('should reject missing token or password', async () => {
      const response = await request(app)
        .post('/api/auth/reset/confirm')
        .query({});

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('Token and new password are required');
    });
  });
});
