CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  email TEXT UNIQUE,
  password_hash TEXT,
  is_verified BOOLEAN DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE verification (
  user_id INTEGER,
  token TEXT,
  expires INTEGER,
  FOREIGN KEY(user_id) REFERENCES users(id));

CREATE TABLE password_reset (
  user_id INTEGER,
  token TEXT,
  expires INTEGER,
  FOREIGN KEY(user_id) REFERENCES users(id));