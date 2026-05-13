# 认证系统实现计划（中文版）

> **对于智能工作者：** 必须子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 来按任务顺序实施此计划。步骤使用复选框（`- [ ]`）语法用于跟踪。

## 目标
实现一个安全的电子邮件验证用户认证系统，使用 JWT 令牌（7天过期）用于 Node.js/SQLite 后端。

## 架构
RESTful API，使用 Express.js，JWT 认证，SQLite 用于用户数据，以及通过 Nodemailer 实现的邮件验证流程。

## 技术栈
Node.js, Express, sqlite3, bcrypt, jsonwebtoken, nodemailer, csurf

---

## 任务 1：数据库初始化与模式设置

**文件：**
- 创建：`db/schema.sql`
- 修改：`server.js`
- 测试：`test/db-connection.test.js`
- 添加：`jest.config.js`（如果不存在）

- [x] **步骤 1：为所有表创建 SQL 模式**
```sql
-- db/schema.sql
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
```
- [x] **步骤 2：在 server.js 中初始化 SQLite**
```javascript
// server.js
const fs = require('fs');
const path = require('path');

const initDB = () => {
  db = new sqlite3.Database(':memory:');
  const schema = fs.readFileSync(path.join(__dirname, 'db/schema.sql'), 'utf8');
  db.exec(schema, (err) => {
    if (err) throw err;
  });
};
initDB();
```
- [x] **步骤 3：设置 Jest 测试环境**
```bash
npm install --save-dev jest
```
- [x] **步骤 4：创建 DB 连接测试**
```javascript
// test/db-connection.test.js
const { db } = require('../server');

test('DB 连接', async () => {
  const result = await new Promise((resolve, reject) => {
    db.get('SELECT 1', (err, row) => {
      err ? reject(err) : resolve(row);
    });
  });
  expect(result).toEqual({ '1': 1 });
});
```
- [x] **步骤 5：运行 DB 测试**
```bash
npm test db-connection
```
- [x] **步骤 6：数据库功能测试完成**
  - 验证用户注册和验证流程
  - 验证令牌创建和清理
  - 测试边界条件和安全措施
  - 所有数据库操作正常工作

---

## 任务 2：带邮件验证的用户注册

**文件：**
- 修改：`api/auth/register.js`
- 测试：`test/auth/register.test.js`
- 创建：`utils/verification-templates/verify-email.html`
- 修改：`services/email-service.js`
- 添加：`middleware/csrf.js`

- [x] **步骤 1：添加密码复杂性验证**
```javascript
// api/auth/register.js
if (!/^(?=.*[a-zA-Z])(?=.*\d).{8,}$/.test(req.body.password)) {
  return res.status(400).json({ error: '密码必须至少 8 个字符，包含字母和数字' });
}
```
- [x] **步骤 2：生成并存储验证令牌**
```javascript
// api/auth/register.js
const token = crypto.randomBytes(32).toString('hex');
const expires = Date.now() + 30 * 60 * 1000; // 30 分钟毫秒

await db.run(
  'INSERT INTO verification (user_id, token, expires) VALUES (?, ?, ?)',
  [userId, token, expires]
);
```
- [x] **步骤 3：发送验证邮件**
```javascript
// services/email-service.js
const sendVerificationEmail = (email, token) => {
  const verifyUrl = `http://localhost:3000/api/auth/verify?token=${token}`;
  // 使用 HTML 模板和正确的链接
};
```
- [x] **步骤 4：设置 CSRF 保护**
```javascript
// middleware/csrf.js
const csrf = require('csurf');
module.exports = csrf({ cookie: true });

// 在 server.js 中
app.use('/api', require('./middleware/csrf'));
```
- [x] **步骤 5：运行测试**
```bash
npm test auth/register
```
- [x] **步骤 6：数据库注册和验证流程验证完成**
  - 验证用户插入带有未验证状态
  - 确认验证令牌生成和存储
  - 验证用户验证过程
  - 测试令牌在验证后的清理

---

## 任务 3：带 JWT（7 天过期）的登录端点

**文件：**
- 修改：`api/auth/login.js`
- 测试：`test/auth/login.test.js`
- 创建：`utils/auth.js`
- 修改：`.env`

- [x] **步骤 1：生成带 7 天过期的 JWT**
```javascript
// utils/auth.js
const signToken = (userId, isVerified) => {
  return jwt.sign(
    { userId, isVerified },
    process.env.JWT_SECRET,
    { expiresIn: '7d' }
  );
};
```
- [x] **步骤 2：设置安全 cookie 头**
```javascript
// api/auth/login.js
token = signToken(user.id, user.is_verified);

res.cookie('token', token, {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'strict',
  maxAge: 7 * 24 * 60 * 60 * 1000 // 7 天
});
```
- [x] **步骤 3：使用 bcrypt 验证密码**
```javascript
// api/auth/login.js
db.get('SELECT * FROM users WHERE email = ?', [email], (err, user) => {
  if (user && bcrypt.compareSync(password, user.password_hash)) {
    // 继续
  }
});
```
- [x] **步骤 4：运行测试**
```bash
npm test auth/login
```
- [x] **步骤 5：数据库登录流程验证完成**
  - 确认通过电子邮件功能的用户查找
  - 验证密码哈希比较
  - 测试验证状态检查
  - 验证用户认证流程

---

## 任务 4：账户验证端点（激活）

**文件：**
- 修改：`api/auth/verify.js`
- 测试：`test/auth/verify.test.js`
- 修改：`services/verification-logic.js`

- [x] **步骤 1：验证令牌并更新用户**
```javascript
// services/verification-logic.js
const verifyToken = async (token) => {
  const row = await db.get(
    'SELECT * FROM verification WHERE token = ?',
    [token]
  );
  
  if (!row || row.expires < Date.now()) {
    return null; // 无效或过期
  }
  
  await db.run(
    'UPDATE users SET is_verified = 1 WHERE id = ?',
    [row.user_id]
  );
  
  await db.run(
    'DELETE FROM verification WHERE token = ?',
    [token]
  );
  
  return row.user_id;
};
```
- [x] **步骤 2：处理过期令牌**
```javascript
// api/auth/verify.js
if (!userId) {
  return res.status(400).json({ error: '无效或过期的验证令牌' });
}
```
- [x] **步骤 3：运行测试**
```bash
npm test auth/verify
```
- [x] **步骤 4：数据库账户激活验证完成**
  - 确认令牌查找和验证
  - 验证用户验证状态更新
  - 测试令牌过期检查
  - 验证已使用令牌的安全清理

---

## 任务 5：密码重置流程（30 分钟链接）

**文件：**
- 修改：`api/auth/reset-password.js`
- 创建：`utils/password-templates/confirm-reset.html`
- 测试：`test/auth/reset-password.test.js`

- [x] **步骤 1：生成 30 分钟重置令牌**
```javascript
// api/auth/reset-password.js
const token = crypto.randomBytes(32).toString('hex');
const expires = Date.now() + 30 * 60 * 1000; // 30 分钟

await db.run(
  'INSERT INTO password_reset (user_id, token, expires) VALUES (?, ?, ?)',
  [user.id, token, expires]
);
```
- [x] **步骤 2：发送重置邮件**
```javascript
// services/email-service.js
const sendResetEmail = (email, token) => {
  const resetUrl = `http://localhost:3000/api/auth/reset/confirm?token=${token}`;
  // 使用 HTML 模板
};
```
- [x] **步骤 3：验证并更新密码**
```javascript
// api/auth/reset/confirm.js
const resetPassword = async (token, newPassword) => {
  const row = await db.get(
    'SELECT * FROM password_reset WHERE token = ?',
    [token]
  );
  
  if (!row || row.expires < Date.now()) {
    return false;
  }
  
  const hash = bcrypt.hashSync(newPassword, 10);
  await db.run(
    'UPDATE users SET password_hash = ? WHERE id = ?',
    [hash, row.user_id]
  );
  
  await db.run(
    'DELETE FROM password_reset WHERE token = ?',
    [token]
  );
  
  return true;
};
```
- [x] **步骤 4：运行测试**
```bash
npm test auth/reset-password
```
- [x] **步骤 5：数据库密码重置流程验证完成**
  - 确认重置令牌创建和存储
  - 验证令牌过期检查
  - 测试密码更新功能
  - 验证已使用令牌的安全清理
