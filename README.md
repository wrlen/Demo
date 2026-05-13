# Smart Customer Service System

基于通义千问（Qwen）大模型的智能客服系统，具备知识库检索、语义缓存、安全防护、多 Agent 协作等核心功能。

## 功能特性

- **多 Agent 架构**：支持路由分发、特定领域 Agent 和通用 Agent 灵活协作
- **知识库检索**：基于 FAQ 和企业政策文档的智能检索
- **语义缓存**：自动缓存相似问答，提升响应速度
- **安全防护**：输入输出内容安全检测与敏感信息过滤
- **API 服务**：提供 RESTful API 接口，支持流式和非流式响应
- **Docker 部署**：支持容器化一键部署

## 项目结构

```
├── main.py              # 入口文件，FastAPI 服务
├── agents.py            # Agent 定义与管理
├── agent_core.py        # Agent 核心逻辑
├── agent_v2.py          # Agent V2 版本
├── agent_with_tools.py  # 集成工具的 Agent
├── api.py               # API 路由层
├── config.py            # 配置管理
├── database.py          # 数据库操作
├── knowledge_base.py    # 知识库管理
├── cache.py             # 语义缓存
├── guard.py             # 安全防护层
├── tools.py             # 工具函数
├── tools_v1.py          # 工具函数 V1
├── logger.py            # 日志系统
├── test_auto.py         # 自动化测试
├── requirements.txt     # Python 依赖
├── Dockerfile           # Docker 构建文件
├── docker-compose.yml   # Docker Compose 配置
├── data/
│   ├── faq.md           # FAQ 知识库
│   └── company_policy.txt  # 企业政策文档
└── .env                 # 环境变量配置
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/Wrlen/Smart-Demo.git
cd Smart-Demo

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```
DASHSCOPE_API_KEY=your_api_key_here
MODEL_NAME=qwen-turbo
```

### 3. 启动服务

```bash
# 方式一：直接运行
python main.py

# 方式二：Docker 部署
docker-compose up -d
```

服务默认运行在 `http://localhost:8000`。

### 4. API 使用

```bash
# 非流式请求
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "user_id": "123"}'

# 流式请求
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "user_id": "123"}'
```

## 技术栈

- **框架**：FastAPI
- **大模型**：通义千问（Qwen）
- **缓存**：语义相似度缓存
- **数据库**：SQLite
- **向量存储**：ChromaDB
- **部署**：Docker / Docker Compose

## License

MIT
