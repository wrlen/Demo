# DOC-ROBOT - 技术文档智能问答与更新系统

基于私有文档的 RAG 问答 + Agent 自动改文档提 PR 的全栈 AI 应用。

## 技术栈

- **后端**: FastAPI
- **LLM**: 阿里云百炼 qvq-max-2025-03-25
- **向量数据库**: ChromaDB
- **Embedding**: BGE (本地模型)
- **前端**: Streamlit
- **文档处理**: LangChain

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

复制 `.env.example` 为 `.env` 并配置你的 API 密钥：

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

### 3. 准备文档

将你的 Markdown 文档放入 `data/docs/` 目录。

### 4. 数据入库

首次运行前需要对文档进行向量化：

```bash
python -c "from modules.loader import run; run()"
```

### 5. 启动服务

**启动后端服务**:
```bash
uvicorn main:app --reload --port 8000
```

**启动前端界面**:
```bash
cd frontend
streamlit run app.py --server.port 8501
```

## 架构改进记录

### 🔧 已完成的改进

#### 1. 依赖版本固定
- 所有依赖使用固定版本号，提高稳定性
- `chromadb` 固定为 `0.6.3`，避免兼容问题

#### 2. 日志记录系统
- 新增 `modules/logger.py`
- 支持控制台和文件双输出
- 日志文件自动轮转 (10MB × 5)
- 所有 API 接入日志记录

#### 3. 会话隔离修复
- 使用 `session_id` 隔离用户状态
- 修复多用户下 `pending_updates` 混淆问题
- 前端自动生成 UUID 作为会话标识

#### 4. 项目配置完善
- 新增 `.gitignore` 文件
- 改进模块初始化 `__init__.py`
- 添加版本信息

## API 接口

### `/chat` - 智能问答
```python
POST /chat
{
  "question": "如何配置数据库？",
  "session_id": "uuid"
}
```

### `/agent` - 文档更新分析
```python
POST /agent
{
  "changelog": "## 更新内容\n- 修改 API 地址...",
  "session_id": "uuid"
}
```

### `/agent/confirm` - 确认提交变更
```python
POST /agent/confirm
{
  "confirmed_files": ["api-guide.md"],
  "session_id": "uuid"
}
```

### `/feedback` - 用户反馈
```python
POST /feedback
{
  "question": "...",
  "answer": "...",
  "rating": "up"
}
```

## 项目结构

```
doc-robot/
├── main.py                 # FastAPI 入口
├── config.py              # 配置管理
├── requirements.txt       # 依赖清单
├── .env.example          # 环境变量模板
├── modules/
│   ├── __init__.py       # 模块初始化
│   ├── logger.py         # 日志系统 ✨
│   ├── loader.py         # 文档加载与向量化
│   ├── retriever.py      # 混合检索与重排序
│   ├── qa.py             # RAG 问答与记忆
│   ├── agent.py          # 文档更新 Agent
│   ├── tools.py          # Agent 工具函数
│   └── guard.py          # 安全护栏
├── data/docs/            # 文档目录
├── chroma_db/            # 向量数据库
├── frontend/             # Streamlit 前端
└── tests/                # 测试目录
```

## 安全特性

- ✅ 输入护栏：检查查询长度和潜在注入
- ✅ 输出护栏：拦截疑似幻觉的回答
- ✅ 会话隔离：多用户状态互不干扰
- ✅ 路径白名单：仅允许操作文档目录
- ✅ 配置安全：敏感信息不提交到 Git

## 下一步改进

- [ ] 添加单元测试
- [ ] 实现对话记忆持久化 (Redis)
- [ ] 改进 Agent 输出解析 (结构化输出)
- [ ] 添加 Prometheus 监控指标
- [ ] 完善 Docker 部署
- [ ] 实现向量库增量更新
