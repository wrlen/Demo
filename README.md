# Claude-Demo - 认证系统实现

此文件夹包含认证系统实现项目的所有相关文件，如原始项目计划文档中所述。

## 项目概述

一个安全的、带邮箱验证的用户认证系统，使用 JWT 令牌（7天有效期），基于 Node.js/SQLite 后端。

**架构：** RESTful API 配合 Express.js、JWT 认证、SQLite 用户数据存储，以及通过 Nodemailer 实现的邮件验证流程。

**技术栈：** Node.js、Express、sqlite3、bcrypt、jsonwebtoken、nodemailer、csurf

## 文件结构

```
Claude-Demo/
├── server.js                 # 主服务器入口点
├── package.json             # 项目依赖和脚本
├── jest.config.js           # Jest 测试配置
├── db/
│   ├── schema.sql           # 数据库表结构定义
│   └── database.js          # 数据库连接和工具函数
├── api/
│   └── auth/                # 认证 API 端点
│       ├── register.js      # 用户注册（带邮箱验证）
│       ├── login.js         # 登录端点（JWT 7天有效期）
│       ├── verify.js        # 账户验证端点
│       ├── reset-password.js # 密码重置请求
│       └── confirm-reset.js # 密码重置确认
├── test/                    # 测试文件
│   ├── db-connection.test.js
│   └── auth/                # 认证测试
│       ├── register.test.js
│       ├── login.test.js
│       ├── verify.test.js
│       └── reset-password.test.js
├── utils/
│   └── auth.js              # 认证工具函数（JWT 处理）
├── services/
│   └── email-service.js     # 邮件服务（用于验证和密码重置）
├── middleware/
│   └── csrf.js              # CSRF 保护中间件
└── docs/
    ├── auth-system-implementation.md      # 原始英文实现计划
    └── auth-system-implementation-zh.md   # 中文版实现计划
```

## 快速开始

1. 安装依赖：`npm install`
2. 运行测试：`npm test`
3. 启动服务器：`npm start`

## 已实现功能

- ✅ 数据库初始化和表结构设置
- ✅ 用户注册（带邮箱验证）
- ✅ 登录端点（JWT 7天有效期）
- ✅ 账户验证端点（激活）
- ✅ 密码重置流程（30分钟链接有效期）