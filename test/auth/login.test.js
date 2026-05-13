const request = require('supertest');
const { app, db, _clear } = require('../../server');

describe('Authentication Login Tests', () => {
  beforeEach(() => {
    _clear();
  });

  describe('POST /api/auth/login', () => {
    test('should login with valid credentials', async () => {
      // First register a user
      await request(app).post('/api/auth/register').send({
        email: 'login@test.com',
        password: 'password123'
      });

      const response = await request(app)
        .post('/api/auth/login')
        .send({
          email: 'login@test.com',
          password: 'password123'
        });

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('token');
      expect(response.body.user.email).toBe('login@test.com');
      expect(response.body.user.isVerified).toBe(false);
    });

    test('should reject invalid email', async () => {
      const response = await request(app)
        .post('/api/auth/login')
        .send({
          email: 'nonexistent@test.com',
          password: 'password123'
        });

      expect(response.status).toBe(401);
      expect(response.body.error).toBe('Invalid email or password');
    });

    test('should reject wrong password', async () => {
      // First register a user
      await request(app).post('/api/auth/register').send({
        email: 'wrongpass@test.com',
        password: 'password123'
      });

      const response = await request(app)
        .post('/api/auth/login')
        .send({
          email: 'wrongpass@test.com',
          password: 'wrongpassword'
        });

      expect(response.status).toBe(401);
      expect(response.body.error).toBe('Invalid email or password');
    });

    test('should reject missing credentials', async () => {
      const response = await request(app)
        .post('/api/auth/login')
        .send({});

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('Email and password are required');
    });
  });
});
