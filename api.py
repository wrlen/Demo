"""
api.py - 智能客服 API 服务
================================================================================
【为什么需要 API 化？】

现在的 main.py 是 Streamlit 界面，只能人在浏览器里用。
API 化之后：
- 其他程序可以调用你的智能体（如微信机器人、网页插件）
- 前端和后端分离，更灵活
- 可以水平扩展（多台服务器同时跑）

【FastAPI 是什么？】
Python 最流行的 API 框架之一：
- 自动生成接口文档（/docs）
- 异步支持，性能好
- 简单易学
================================================================================
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent_with_tools import AgentWithTools
import uvicorn

# ===== 创建 FastAPI 应用 =====
app = FastAPI(
    title="智能客服 API",
    description="极客科技智能客服后端服务",
    version="2.0.0"
)

# ===== 允许跨域访问（让前端网页能调用） =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境要限制具体域名
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 全局智能体实例（启动时初始化一次） =====
agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    global agent
    # 🆕 自动初始化数据库（如果表不存在）
    from database import Database
    db = Database()
    db.connect()
    cursor = db.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
    if not cursor.fetchone():
        db.init_tables()
        db.insert_sample_data()
        print("🆕 数据库已自动初始化")
    db.close()

    agent = AgentWithTools(use_multi_agent=True)
    print("🚀 智能客服 API 已启动！")
    yield
    # 关闭时执行（如果需要清理资源在这里写）
    print("👋 服务已关闭")

# 然后把 FastAPI 的创建改为：
app = FastAPI(
    title="智能客服 API",
    description="极客科技智能客服后端服务",
    version="2.0.0",
    lifespan=lifespan  # ← 加这个参数
)


# ===== 定义请求和响应格式 =====

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    user_id: str = "anonymous"  # 用户标识（可选）


class ChatResponse(BaseModel):
    """聊天响应"""
    reply: str
    cached: bool = False


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str


# ===== API 接口 =====

@app.get("/", response_model=HealthResponse)
async def root():
    """根路径 - 健康检查"""
    return {
        "status": "running",
        "version": "2.0.0"
    }


@app.get("/health")
async def health():
    """健康检查"""
    kb_loaded = agent.kb.vector_store is not None if agent else False
    return {
        "status": "healthy",
        "knowledge_base": kb_loaded,
        "model": "qwen-turbo"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天接口

    请求示例：
    {
        "message": "帮我查下订单12345",
        "user_id": "user_001"
    }

    响应示例：
    {
        "reply": "您好！订单12345...",
        "cached": false
    }
    """
    if not agent:
        return {"reply": "服务未就绪", "cached": False}

    # 调用智能体
    reply = agent.chat(request.message)

    return {
        "reply": reply,
        "cached": False
    }


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天接口（逐字返回）
    用于需要打字机效果的场景
    """
    from fastapi.responses import StreamingResponse

    if not agent:
        return StreamingResponse(iter(["服务未就绪"]), media_type="text/plain")

    return StreamingResponse(
        agent.chat_stream(request.message),
        media_type="text/plain"
    )


@app.get("/stats")
async def stats():
    """获取统计数据"""
    if not agent or not hasattr(agent, 'logger'):
        return {"error": "日志模块未就绪"}

    return agent.logger.get_stats()


# ===== 启动入口 =====
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 启动智能客服 API 服务")
    print("=" * 50)
    print(f"📍 地址: http://localhost:8000")
    print(f"📖 文档: http://localhost:8000/docs")
    print("=" * 50)

    uvicorn.run(
        "api:app",
        host="0.0.0.0",  # 允许外部访问
        port=8000,
        reload=True  # 代码修改后自动重启
    )