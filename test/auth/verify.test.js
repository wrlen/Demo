const request = require('supertest');
const { app, db, _clear } = require('../../server');

describe('Authentication Verification Tests', () => {
  beforeEach(() => {
    _clear();
  });

  describe('GET /api/auth/verify', () => {
    test('should verify email with valid token', async () => {
      // First register a user
      const regResponse = await request(app).post('/api/auth/register').send({
        email: 'verify@test.com',
        password: 'password123'
      });

      const userId = regResponse.body.user.id;

      // Manually insert verification token for testing
      const token = 'test-verification-token-12345';
      const expires = Date.now() + 30 * 60 * 1000; // 30 minutes from now

      await new Promise((resolve, reject) => {
        db.run(
          'INSERT INTO verification (user_id, token, expires) VALUES (?, ?, ?)',
          [userId, token, expires],
          function(err) { err ? reject(err) : resolve(); }
        );
      });

      const response = await request(app)
        .get('/api/auth/verify')
        .query({ token });

      expect(response.status).toBe(200);
      expect(response.body.verified).toBe(true);

      // Verify user is now marked as verified
      const user = await new Promise((resolve, reject) => {
        db.get('SELECT is_verified FROM users WHERE id = ?', [userId], (err, row) => {
          err ? reject(err) : resolve(row);
        });
      });

      expect(user.is_verified).toBe(1);
    });

    test('should reject invalid token', async () => {
      const response = await request(app)
        .get('/api/auth/verify')
        .query({ token: 'invalid-token' });

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('Invalid verification token');
    });

    test('should reject expired token', async () => {
      // Register a user
      const regResponse = await request(app).post('/api/auth/register').send({
        email: 'expired@test.com',
        password: 'password123'
      });

      const userId = regResponse.body.user.id;

      // Insert expired token
      const expiredToken = 'expired-token-12345';
      const pastTime = Date.now() - 1000 * 60 * 5; // 5 minutes ago

      await new Promise((resolve, reject) => {
        db.run(
          'INSERT INTO verification (user_id, token, expires) VALUES (?, ?, ?)',
          [userId, expiredToken, pastTime],
          function(err) { err ? reject(err) : resolve(); }
        );
      });

      const response = await request(app)
        .get('/api/auth/verify')
        .query({ token: expiredToken });

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('Verification token has expired');
    });

    test('should reject missing token', async () => {
      const response = await request(app)
        .get('/api/auth/verify')
        .query({});

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('Verification token is required');
    });
  });
});
