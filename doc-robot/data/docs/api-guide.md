# API 接口文档

## 认证方式

系统使用 OAuth 2.0 进行身份认证。在请求头中携带 Token：

```
Authorization: Bearer <access_token>
```

Token 有效期 2 小时，过期后需用 refresh_token 刷新。

### 获取 Token

POST /auth/login

请求体：
- username: 用户名
- password: 密码

返回值：
- access_token
- refresh_token
- expires_in: 7200

## 接口列表

### 用户管理

#### GET /users

获取用户列表，支持分页查询。

参数：
- page: 页码（默认1）
- page_size: 每页数量（默认20）
- keyword: 搜索关键词

#### POST /users

创建新用户。

请求体：
- username: 用户名（必填）
- email: 邮箱（必填）
- role: 角色（admin/user，默认user）

### 数据查询

#### GET /data/query

执行数据查询。

参数：
- sql: 查询语句（受限语法）
- database: 目标数据库名

返回 JSON 格式结果，最大返回 1000 条。