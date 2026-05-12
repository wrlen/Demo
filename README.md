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
