# 漫剧自动化工作台 - 技术参考文档

## 目录

1. [项目概述](#1-项目概述)
   - 1.1 项目简介
   - 1.2 技术栈
   - 1.3 核心功能

2. [架构说明](#2-架构说明)
   - 2.1 系统架构图
   - 2.2 模块划分
   - 2.3 数据流程

3. [API接口说明](#3-api接口说明)
   - 3.1 项目管理接口
   - 3.2 剧本解析接口
   - 3.3 分镜管理接口
   - 3.4 角色管理接口
   - 3.5 任务管理接口

---

## 1. 项目概述

### 1.1 项目简介

**漫剧自动化工作台**是一个基于AI技术的漫画/动画剧本创作与制作平台。该平台提供从剧本解析、分镜生成到角色设计、图像渲染的完整工作流，旨在帮助创作者快速将文字剧本转化为可视化的漫画内容。

### 1.2 技术栈

| 分类 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **前端** | Next.js | 14.x | React服务端渲染框架 |
| | TypeScript | 5.x | 类型安全 |
| | TailwindCSS | 3.x | 样式框架 |
| **后端** | FastAPI | 0.104.x | Python Web框架 |
| | SQLAlchemy | 2.x | ORM工具 |
| | SQLite | 3.x | 轻量级数据库 |
| | Celery | 5.x | 异步任务队列 |
| | Redis | 7.x | 消息代理 |
| **AI服务** | DashScope | - | 阿里云大模型服务 |

### 1.3 核心功能

| 功能模块 | 说明 |
|---------|------|
| **剧本解析** | 将自然语言剧本转换为结构化数据（对话、旁白、动作、角色） |
| **分镜生成** | 根据剧本自动生成分镜描述和镜头配置 |
| **角色管理** | 角色信息管理、角色三视图生成 |
| **图像生成** | 基于AI的图像渲染 |
| **配音生成** | 自动生成字幕和配音 |
| **视频合成** | 将分镜合成为完整视频 |

---

## 2. 架构说明

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         前端层 (Frontend)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │  Home Page  │  │ Characters  │  │ Storyboard  │               │
│  │  (剧本输入) │  │  (角色管理)  │  │  (分镜编辑)  │               │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘               │
│         │                │                │                         │
└─────────┼────────────────┼────────────────┼─────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API网关层 (FastAPI)                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  main.py - REST API Endpoints                               │   │
│  │  - CORS中间件                                              │   │
│  │  - WebSocket实时通信                                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│    业务逻辑层     │ │     数据访问层    │ │    异步任务层     │
│  ┌─────────────┐  │ │  ┌─────────────┐  │ │  ┌─────────────┐  │
│  │ WriterAgent │  │ │  │  Database   │  │ │  │  Celery     │  │
│  │ Director    │  │ │  │  Session    │  │ │  │  Tasks      │  │
│  │ ArtistAgent │  │ │  └─────────────┘  │ │  └─────────────┘  │
│  │ VoiceAgent  │  │ │                   │ │                   │
│  └─────────────┘  │ └───────────────────┘ └───────────────────┘
└───────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         外部服务层                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │  DashScope  │  │   SQLite    │  │   Redis     │               │
│  │  (LLM API)  │  │  (数据库)   │  │ (消息队列)   │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 模块划分

#### 2.2.1 目录结构

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
└── docs/                     # 项目文档
    └── TECHNICAL_REFERENCE.md # 技术参考文档
```

#### 2.2.2 核心模块职责

| 模块 | 文件 | 职责描述 |
|------|------|---------|
| **API网关** | `main.py` | REST API入口，路由分发，请求处理 |
| **数据模型** | `models.py` | Pydantic数据结构定义 |
| **数据库** | `database.py` | SQLAlchemy配置，会话管理 |
| **异步任务** | `tasks.py` | Celery任务定义 |
| **剧本解析** | `writer_agent.py` | LLM调用，剧本结构化解析 |
| **分镜生成** | `director_agent.py` | 分镜脚本生成 |
| **图像生成** | `artist_agent.py` | AI图像生成 |
| **配音生成** | `voice_agent.py` | 语音合成，字幕生成 |

### 2.3 数据流程

#### 2.3.1 剧本解析流程

```
用户输入剧本 ──► POST /projects/{id}/script ──► WriterAgent ──► LLM API
                                                               │
                                                               ▼
                                                      返回结构化剧本
                                                               │
                                                               ▼
                                         ┌───────────────┬───────────────┐
                                         ▼               ▼               ▼
                                      对话列表         旁白列表        角色列表
```

#### 2.3.2 分镜生成流程

```
结构化剧本 ──► POST /projects/{id}/storyboard ──► DirectorAgent
                                                      │
                                                      ▼
                                               生成分镜数据
                                                      │
                                                      ▼
                                         ┌───────────────┬───────────────┐
                                         ▼               ▼               ▼
                                      镜头描述         场景类型        角色情绪
```

---

## 3. API接口说明

### 3.1 项目管理接口

#### 3.1.1 创建项目

| 属性 | 值 |
|------|-----|
| **路径** | `POST /projects` |
| **描述** | 创建新的项目 |
| **Content-Type** | `application/x-www-form-urlencoded` |

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 项目标题 |
| `description` | string | 否 | 项目描述 |

**响应示例：**

```json
{
  "id": "5abf0276-334b-49c8-bfc4-62a68624ef5a",
  "title": "剧本项目",
  "description": "自动生成",
  "created_at": "2026-05-11T16:41:24.277374"
}
```

#### 3.1.2 获取项目详情

| 属性 | 值 |
|------|-----|
| **路径** | `GET /projects/{project_id}` |
| **描述** | 获取指定项目的详细信息 |

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `project_id` | string | 项目ID |

**响应示例：**

```json
{
  "id": "5abf0276-334b-49c8-bfc4-62a68624ef5a",
  "title": "剧本项目",
  "description": "自动生成",
  "created_at": "2026-05-11T16:41:24.277374"
}
```

#### 3.1.3 列出所有项目

| 属性 | 值 |
|------|-----|
| **路径** | `GET /projects` |
| **描述** | 获取所有项目列表 |

**响应示例：**

```json
[
  {
    "id": "5abf0276-334b-49c8-bfc4-62a68624ef5a",
    "title": "剧本项目",
    "description": "自动生成",
    "created_at": "2026-05-11T16:41:24.277374"
  }
]
```

---

### 3.2 剧本解析接口

#### 3.2.1 解析剧本

| 属性 | 值 |
|------|-----|
| **路径** | `POST /projects/{project_id}/script` |
| **描述** | 将自然语言剧本解析为结构化数据 |
| **Content-Type** | `application/json` |

**请求体：**

```json
{
  "raw_text": "张三：你好！\n李四：你好！"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `raw_text` | string | 是 | 原始剧本文本 |

**响应示例：**

```json
{
  "dialogues": [
    {"speaker": "张三", "text": "你好！", "position": "center"},
    {"speaker": "李四", "text": "你好！", "position": "center"}
  ],
  "narrations": [],
  "actions": [],
  "characters": [
    {"name": "张三", "description": "从对话中可以看出，张三是一个礼貌的人"},
    {"name": "李四", "description": "同样地，李四也展现出了基本的礼节"}
  ]
}
```

**数据模型定义：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `dialogues` | array | 对话列表 |
| `dialogues[].speaker` | string | 说话者名称 |
| `dialogues[].text` | string | 对话内容 |
| `dialogues[].position` | string | 显示位置(center/left/right) |
| `narrations` | array | 旁白列表 |
| `narrations[].text` | string | 旁白内容 |
| `narrations[].position` | string | 显示位置 |
| `actions` | array | 动作列表 |
| `actions[].description` | string | 动作描述 |
| `characters` | array | 角色列表 |
| `characters[].name` | string | 角色名称 |
| `characters[].description` | string | 角色描述 |

---

### 3.3 分镜管理接口

#### 3.3.1 生成分镜

| 属性 | 值 |
|------|-----|
| **路径** | `POST /projects/{project_id}/storyboard` |
| **描述** | 根据剧本生成分镜 |
| **Content-Type** | `application/json` |

**请求体：** 同剧本解析响应结构

**响应示例：**

```json
{
  "shots": [
    {
      "shot_id": 1,
      "scene_type": "全景",
      "duration": 3.5,
      "camera_movement": "固定",
      "visual_description": "室内场景，张三和李四面对面站立",
      "character_emotion": "友好",
      "dialogue": "张三：你好！",
      "narration": "",
      "image_url": null
    }
  ]
}
```

#### 3.3.2 获取分镜列表

| 属性 | 值 |
|------|-----|
| **路径** | `GET /projects/{project_id}/storyboard` |
| **描述** | 获取项目的分镜列表 |

**响应示例：**

```json
{
  "shots": [
    {
      "shot_id": 1,
      "scene_type": "全景",
      "duration": 3.5,
      "camera_movement": "固定",
      "visual_description": "室内场景...",
      "character_emotion": "友好",
      "dialogue": "张三：你好！",
      "narration": "",
      "image_url": "/static/images/project1/1.png"
    }
  ]
}
```

#### 3.3.3 更新分镜

| 属性 | 值 |
|------|-----|
| **路径** | `PUT /projects/{project_id}/storyboard/{shot_id}` |
| **描述** | 更新指定分镜的属性 |
| **Content-Type** | `application/json` |

**请求体：**

```json
{
  "scene_type": "中景",
  "duration": 4.0,
  "camera_movement": "推近",
  "visual_description": "更新后的描述",
  "character_emotion": "开心",
  "dialogue": "修改后的对话",
  "narration": "旁白内容"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scene_type` | string | 否 | 场景类型 |
| `duration` | float | 否 | 时长(秒) |
| `camera_movement` | string | 否 | 镜头运动 |
| `visual_description` | string | 否 | 视觉描述 |
| `character_emotion` | string | 否 | 角色情绪 |
| `dialogue` | string | 否 | 对话内容 |
| `narration` | string | 否 | 旁白内容 |

**响应示例：** 返回更新后的完整分镜列表

---

### 3.4 角色管理接口

#### 3.4.1 添加角色

| 属性 | 值 |
|------|-----|
| **路径** | `POST /projects/{project_id}/characters` |
| **描述** | 批量添加角色到项目 |
| **Content-Type** | `application/json` |

**请求体：**

```json
[
  {
    "name": "张三",
    "description": "一个友好的年轻人"
  },
  {
    "name": "李四",
    "description": "同样友好的年轻人"
  }
]
```

**响应示例：**

```json
{
  "characters": [
    {
      "id": "uuid-1",
      "name": "张三",
      "description": "一个友好的年轻人"
    }
  ]
}
```

#### 3.4.2 获取角色列表

| 属性 | 值 |
|------|-----|
| **路径** | `GET /projects/{project_id}/characters` |
| **描述** | 获取项目的角色列表及参考图 |

**响应示例：**

```json
{
  "characters": [
    {
      "id": "uuid-1",
      "name": "张三",
      "description": "一个友好的年轻人",
      "references": [
        {"id": "ref-1", "view_type": "front", "image_url": "/static/char1_front.png"},
        {"id": "ref-2", "view_type": "side", "image_url": "/static/char1_side.png"},
        {"id": "ref-3", "view_type": "back", "image_url": "/static/char1_back.png"}
      ]
    }
  ]
}
```

#### 3.4.3 生成角色三视图

| 属性 | 值 |
|------|-----|
| **路径** | `POST /projects/{project_id}/characters/{character_id}/generate` |
| **描述** | 异步生成角色的正、侧、背三视图 |

**响应示例：**

```json
{
  "status": "started",
  "message": "正在生成角色三视图"
}
```

---

### 3.5 任务管理接口

#### 3.5.1 生成图像

| 属性 | 值 |
|------|-----|
| **路径** | `POST /projects/{project_id}/generate-images` |
| **描述** | 异步批量生成分镜图像 |

**响应示例：**

```json
{
  "status": "started",
  "message": "正在批量生图"
}
```

#### 3.5.2 重绘单帧

| 属性 | 值 |
|------|-----|
| **路径** | `POST /projects/{project_id}/storyboard/{shot_id}/regenerate` |
| **描述** | 重新生成指定分镜的图像 |

**响应示例：**

```json
{
  "status": "started",
  "message": "正在重绘该镜头"
}
```

#### 3.5.3 生成配音

| 属性 | 值 |
|------|-----|
| **路径** | `POST /projects/{project_id}/generate-voice` |
| **描述** | 生成剧本的配音和字幕 |

**请求体：** 同剧本解析响应结构

**响应示例：**

```json
{
  "status": "started",
  "message": "正在生成配音"
}
```

#### 3.5.4 获取任务列表

| 属性 | 值 |
|------|-----|
| **路径** | `GET /projects/{project_id}/tasks` |
| **描述** | 获取项目的任务列表和状态 |

**响应示例：**

```json
{
  "tasks": [
    {
      "id": "task-uuid",
      "task_type": "GENERATE_IMAGES",
      "status": "COMPLETED",
      "progress": 100,
      "message": null,
      "result": {"message": "图片生成完成"}
    }
  ]
}
```

**任务类型枚举：**

| 类型 | 说明 |
|------|------|
| `GENERATE_IMAGES` | 批量生图 |
| `REGENERATE_SHOT` | 重绘单帧 |
| `GENERATE_VOICE` | 生成配音 |
| `GENERATE_CHARACTER` | 生成角色 |
| `COMPOSE` | 视频合成 |

**任务状态枚举：**

| 状态 | 说明 |
|------|------|
| `RUNNING` | 运行中 |
| `COMPLETED` | 已完成 |
| `FAILED` | 失败 |

---

## 4. 数据库模型

### 4.1 核心数据表

#### 4.1.1 projects 表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PRIMARY KEY | 项目UUID |
| `title` | VARCHAR(255) | NOT NULL | 项目标题 |
| `description` | TEXT | | 项目描述 |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### 4.1.2 shots 表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PRIMARY KEY | 镜头UUID |
| `project_id` | VARCHAR(36) | FOREIGN KEY | 所属项目 |
| `shot_id` | INTEGER | NOT NULL | 镜头序号 |
| `scene_type` | VARCHAR(50) | | 场景类型 |
| `duration` | FLOAT | | 时长(秒) |
| `camera_movement` | VARCHAR(50) | | 镜头运动 |
| `visual_description` | TEXT | | 视觉描述 |
| `character_emotion` | VARCHAR(50) | | 角色情绪 |
| `dialogue` | TEXT | | 对话内容 |
| `narration` | TEXT | | 旁白内容 |
| `image_url` | VARCHAR(500) | | 图像URL |

#### 4.1.3 characters 表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PRIMARY KEY | 角色UUID |
| `project_id` | VARCHAR(36) | FOREIGN KEY | 所属项目 |
| `name` | VARCHAR(100) | NOT NULL | 角色名称 |
| `description` | TEXT | | 角色描述 |

#### 4.1.4 character_references 表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PRIMARY KEY | 参考图UUID |
| `character_id` | VARCHAR(36) | FOREIGN KEY | 所属角色 |
| `view_type` | VARCHAR(20) | NOT NULL | 视图类型(front/side/back) |
| `image_url` | VARCHAR(500) | | 图像URL |

#### 4.1.5 tasks 表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PRIMARY KEY | 任务UUID |
| `project_id` | VARCHAR(36) | FOREIGN KEY | 所属项目 |
| `task_type` | VARCHAR(50) | NOT NULL | 任务类型 |
| `status` | VARCHAR(20) | NOT NULL | 任务状态 |
| `progress` | INTEGER | DEFAULT 0 | 进度(0-100) |
| `message` | TEXT | | 错误信息 |
| `result` | TEXT | | 任务结果(JSON) |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

## 5. WebSocket接口

### 5.1 实时进度推送

| 属性 | 值 |
|------|-----|
| **路径** | `ws://localhost:8000/ws/{project_id}` |
| **描述** | 实时接收任务进度更新 |

**消息格式：**

```json
{
  "type": "progress",
  "task_id": "task-uuid",
  "progress": 50,
  "message": "正在生成第3张图片"
}
```

```json
{
  "type": "complete",
  "task_id": "task-uuid",
  "result": {"message": "图片生成完成"}
}
```

```json
{
  "type": "error",
  "task_id": "task-uuid",
  "message": "生成失败：网络超时"
}
```

---

## 6. 配置说明

### 6.1 环境变量

后端服务使用 `.env` 文件配置环境变量：

```env
# API配置
API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
API_KEY=your-api-key-here

# Redis配置（Celery消息代理）
REDIS_URL=redis://localhost:6379/0

# 数据库配置
DATABASE_URL=sqlite:///./demo.db

# 服务端口
PORT=8000
```

### 6.2 启动方式

**开发环境：**

```bash
# 启动后端服务
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 启动Celery worker
cd backend
celery -A celery_config worker --loglevel=info

# 启动前端服务
cd frontend
npm run dev
```

**生产环境：**

```bash
# 构建前端
cd frontend
npm run build

# 启动后端（使用gunicorn）
cd backend
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

---

## 7. 错误处理

### 7.1 常见HTTP状态码

| 状态码 | 说明 |
|--------|------|
| `200 OK` | 请求成功 |
| `404 Not Found` | 资源不存在（项目/角色/分镜等） |
| `400 Bad Request` | 请求参数错误 |
| `500 Internal Server Error` | 服务器内部错误 |

### 7.2 错误响应格式

```json
{
  "detail": "项目不存在"
}
```

---

**文档版本**: v1.0  
**创建日期**: 2026-05-12  
**适用范围**: 开发人员参考