# 漫剧自动化工作台

基于AI技术的漫画/动画剧本创作与制作平台，提供从剧本解析、分镜生成到角色设计、图像渲染的完整工作流。

## 功能特性

- 剧本解析：将自然语言剧本转换为结构化数据（对话、旁白、动作、角色）
- 分镜生成：根据剧本自动生成分镜描述和镜头配置
- 角色管理：角色信息管理、角色三视图生成
- 图像生成：基于AI的图像渲染
- 配音生成：自动生成字幕和配音
- 视频合成：将分镜合成为完整视频

## 技术栈

### 前端
- Next.js 14.x - React服务端渲染框架
- TypeScript 5.x - 类型安全
- TailwindCSS 3.x - 样式框架

### 后端
- FastAPI 0.104.x - Python Web框架
- SQLAlchemy 2.x - ORM工具
- SQLite - 轻量级数据库
- Celery 5.x - 异步任务队列
- Redis 7.x - 消息代理

### AI服务
- DashScope - 阿里云大模型服务

## 快速开始

### 前置要求

- Python 3.8+
- Node.js 18+
- Redis 7.x
- 阿里云DashScope API Key

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/your-username/trae-demo.git
cd trae-demo
```

#### 2. 后端安装

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install fastapi uvicorn sqlalchemy celery redis python-dotenv httpx

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API_KEY
```

#### 3. 前端安装

```bash
cd frontend

# 安装依赖
npm install
```

#### 4. 启动Redis服务

```bash
# Windows (使用WSL或Docker)
redis-server

# 或使用Docker
docker run -d -p 6379:6379 redis:7
```

### 运行项目

#### 开发模式

**终端1 - 启动后端服务：**
```bash
cd backend
.venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**终端2 - 启动Celery Worker：**
```bash
cd backend
.venv\Scripts\activate
celery -A celery_config worker --loglevel=info
```

**终端3 - 启动前端服务：**
```bash
cd frontend
npm run dev
```

访问：
- 前端：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

#### 生产模式

**构建前端：**
```bash
cd frontend
npm run build
```

**启动后端（使用gunicorn）：**
```bash
cd backend
.venv\Scripts\activate
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

## 项目结构

```
trae-demo/
├── backend/                    # 后端服务
│   ├── main.py               # FastAPI入口文件
│   ├── models.py             # Pydantic数据模型
│   ├── database.py           # 数据库配置
│   ├── tasks.py              # Celery异步任务
│   ├── celery_config.py      # Celery配置
│   ├── agents/               # AI代理模块
│   │   ├── writer_agent.py  # 剧本解析代理
│   │   ├── director_agent.py # 分镜生成代理
│   │   ├── artist_agent.py   # 图像生成代理
│   │   └── voice_agent.py    # 配音生成代理
│   └── static/               # 静态资源
├── frontend/                  # 前端应用
│   ├── src/
│   │   ├── pages/            # 页面组件
│   │   │   ├── index.tsx     # 首页(剧本输入)
│   │   │   ├── characters.tsx # 角色管理页
│   │   │   └── storyboard.tsx # 分镜编辑页
│   │   └── styles/           # 全局样式
│   ├── next.config.js        # Next.js配置
│   └── package.json          # 依赖配置
├── docs/                     # 项目文档
│   └── TECHNICAL_REFERENCE.md # 技术参考文档
└── README.md                 # 项目说明
```

## 环境变量配置

在 `backend/.env` 文件中配置：

```env
# API配置
API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
API_KEY=your-api-key-here

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 数据库配置
DATABASE_URL=sqlite:///./demo.db

# 服务端口
PORT=8000
```

## API文档

详细的API接口文档请参考：[技术参考文档](docs/TECHNICAL_REFERENCE.md)

主要接口：
- `POST /projects` - 创建项目
- `POST /projects/{id}/script` - 解析剧本
- `POST /projects/{id}/storyboard` - 生成分镜
- `GET /projects/{id}/characters` - 获取角色列表
- `POST /projects/{id}/generate-images` - 生成图像

## GitHub部署

### 方式1：GitHub Actions自动部署到服务器

项目已配置GitHub Actions，可以实现代码推送到GitHub后自动部署到服务器。

#### 配置步骤

1. **创建GitHub仓库**
   - 访问 https://github.com/new
   - 创建新仓库（例如：`trae-demo`）
   - **不要**初始化README、.gitignore或LICENSE

2. **推送代码到GitHub**
   ```bash
   git remote add origin https://github.com/你的用户名/trae-demo.git
   git branch -M main
   git push -u origin main
   ```

3. **配置GitHub Secrets**
   - 进入仓库的 Settings → Secrets and variables → Actions
   - 添加以下Secrets：

   | Secret名称 | 说明 | 示例 |
   |-----------|------|------|
   | `SERVER_HOST` | 服务器IP地址 | `123.456.789.0` |
   | `SERVER_USER` | SSH用户名 | `root` 或 `ubuntu` |
   | `SSH_PRIVATE_KEY` | SSH私钥内容 | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
   | `SSH_PORT` | SSH端口（可选） | `22` |
   | `PROJECT_PATH` | 项目在服务器上的路径 | `/home/user/trae-demo` |
   | `DOCKER_USERNAME` | Docker Hub用户名 | `yourusername` |
   | `DOCKER_PASSWORD` | Docker Hub密码或token | `dckr_pat_...` |

4. **配置服务器SSH密钥**
   ```bash
   # 在本地生成SSH密钥对（如果还没有）
   ssh-keygen -t rsa -b 4096 -C "github-actions"

   # 将公钥复制到服务器
   ssh-copy-id user@your-server-ip

   # 将私钥内容复制到GitHub Secret
   cat ~/.ssh/id_rsa
   ```

5. **触发部署**
   - 推送代码到main分支会自动触发部署
   - 或在GitHub Actions页面手动触发

6. **查看部署状态**
   - 访问仓库的 Actions 页面
   - 查看 "Deploy to Production" 工作流的执行状态

#### GitHub Actions工作流

项目包含三个GitHub Actions工作流：

| 工作流 | 触发条件 | 说明 |
|--------|---------|------|
| `deploy.yml` | 推送到main分支 | 自动部署到生产服务器 |
| `ci.yml` | 推送到任何分支 | 运行测试和代码检查 |
| `docker.yml` | 推送到main分支或打标签 | 构建并推送Docker镜像到Docker Hub |

### 方式2：使用Docker Hub镜像

项目会自动构建Docker镜像并推送到Docker Hub：

```bash
# 拉取最新镜像
docker pull yourusername/trae-backend:latest
docker pull yourusername/trae-celery:latest
docker pull yourusername/trae-frontend:latest

# 使用镜像部署
docker run -d -p 8000:8000 yourusername/trae-backend:latest
```

### 方式3：Vercel部署（仅前端）

1. 访问 https://vercel.com
2. 导入GitHub仓库
3. Vercel会自动检测Next.js并配置
4. 配置环境变量 `NEXT_PUBLIC_API_URL`
5. 点击部署

## Docker部署

### 快速启动

```bash
# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入你的 API_KEY

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 访问应用
# 前端：http://localhost
# 后端API：http://localhost/api
# API文档：http://localhost/api/docs
```

### 服务架构

```
┌─────────────────────────────────────────┐
│           Nginx (端口80)                │
│   反向代理 + 负载均衡 + 静态文件        │
└────────┬──────────────────────────────┘
         │
    ┌────┴────┬──────────────┐
    ▼         ▼              ▼
┌────────┐ ┌────────┐  ┌────────┐
│ 前端   │ │ 后端   │  │ Celery │
│ :3000  │ │ :8000  │  │ Worker │
└────────┘ └───┬────┘  └────────┘
              │
              ▼
         ┌────────┐
         │ Redis  │
         │ :6379  │
         └────────┘
```

### 常用Docker命令

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启特定服务
docker-compose restart backend

# 查看日志
docker-compose logs -f [service-name]

# 进入容器
docker-compose exec backend bash

# 更新并重新构建
docker-compose pull
docker-compose up -d --build

# 清理未使用的资源
docker system prune -a
```

## 详细部署文档

更多部署细节请参考：[部署指南](docs/DEPLOYMENT.md)

## 常见问题

### 1. Redis连接失败

确保Redis服务正在运行：
```bash
redis-cli ping
# 应返回 PONG
```

### 2. API调用失败

检查 `.env` 文件中的 `API_KEY` 是否正确配置。

### 3. 数据库连接池耗尽

已通过FastAPI依赖注入解决，确保使用最新代码。

### 4. 前端构建失败

清除缓存后重试：
```bash
cd frontend
rm -rf .next node_modules
npm install
npm run build
```

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

ISC

## 联系方式

如有问题，请提交Issue或联系项目维护者。
