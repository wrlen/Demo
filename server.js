const express = require('express');
const crypto = require('crypto');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const cookieParser = require('cookie-parser');
const { db, _clear } = require('./db/database');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());
app.use(cookieParser());

const initDB = () => {
  const schema = fs.readFileSync(path.join(__dirname, 'db/schema.sql'), 'utf8');
  db.exec(schema);
  console.log('Database initialized (in-memory)');
};

// Apply CSRF protection to API routes
const csrfProtection = require('./middleware/csrf');
app.use('/api', csrfProtection);

// Register auth routes
app.use('/api/auth/register', require('./api/auth/register'));
app.use('/api/auth/login', require('./api/auth/login'));
app.use('/api/auth/verify', require('./api/auth/verify'));
app.use('/api/auth/reset-password', require('./api/auth/reset-password'));
app.use('/api/auth/reset/confirm', require('./api/auth/confirm-reset'));

initDB();

// Add a simple home page
app.get('/', (req, res) => {
  res.json({
    message: 'Welcome to the Authentication API',
    version: '1.0.0',
    endpoints: {
      register: 'POST /api/auth/register',
      login: 'POST /api/auth/login',
      verify: 'GET /api/auth/verify',
      resetPassword: 'POST /api/auth/reset-password',
      confirmReset: 'POST /api/auth/reset/confirm'
    },
    database: 'In-memory SQLite'
  });
});

if (process.env.NODE_ENV !== 'test' && !process.argv.includes('--test')) {
  const PORT = process.env.PORT || 3000;
  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });
}

module.exports = { app, db, _clear };
