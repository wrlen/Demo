const request = require('supertest');
const { app, db, _clear } = require('../../server');

describe('Authentication Registration Tests', () => {
  beforeEach(() => {
    _clear();
  });

  describe('POST /api/auth/register', () => {
    test('should register a new user with valid data', async () => {
      const response = await request(app)
        .post('/api/auth/register')
        .send({
          email: 'test@example.com',
          password: 'password123'
        });

      expect(response.status).toBe(201);
      expect(response.body).toHaveProperty('message');
      expect(response.body).toHaveProperty('user');
      expect(response.body.user.email).toBe('test@example.com');
      expect(response.body.user.isVerified).toBe(false);

      // Verify user exists in database
      const user = await new Promise((resolve, reject) => {
        db.get('SELECT * FROM users WHERE email = ?', ['test@example.com'], (err, row) => {
          err ? reject(err) : resolve(row);
        });
      });

      expect(user).toBeDefined();
      expect(user.email).toBe('test@example.com');
      expect(user.is_verified).toBe(0);
    });

    test('should reject duplicate email', async () => {
      // Register first user
      await request(app).post('/api/auth/register').send({
        email: 'duplicate@example.com',
        password: 'password123'
      });

      // Try to register again with same email
      const response = await request(app)
        .post('/api/auth/register')
        .send({
          email: 'duplicate@example.com',
          password: 'password456'
        });

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('Email already registered');
    });

    test('should reject weak password', async () => {
      const response = await request(app)
        .post('/api/auth/register')
        .send({
          email: 'weak@example.com',
          password: 'onlyletters'
        });

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('Password must be at least 8 characters with letters and numbers');
    });

    test('should reject invalid email format', async () => {
      const response = await request(app)
        .post('/api/auth/register')
        .send({
          email: 'invalid-email',
          password: 'password123'
        });

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('Invalid email format');
    });

    test('should reject missing email or password', async () => {
      const response1 = await request(app)
        .post('/api/auth/register')
        .send({ password: 'password123' });

      expect(response1.status).toBe(400);

      const response2 = await request(app)
        .post('/api/auth/register')
        .send({ email: 'test@example.com' });

      expect(response2.status).toBe(400);
    });
  });
});
