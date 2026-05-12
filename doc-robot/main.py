from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from modules.qa import get_qa_chat
from modules.agent import run_agent, confirm_and_submit
from modules.guard import check_input, check_output, record_feedback

# ----- 全局状态 -----
_pending_updates: list[dict] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭时的生命周期管理。"""
    # 预热检索器
    try:
        get_qa_chat()
        print("[main] 问答模块已就绪")
    except Exception as e:
        print(f"[main] 检索器初始化警告: {e}")
    yield


app = FastAPI(
    title="技术文档智能问答与自动更新机器人",
    version="1.0.0",
    lifespan=lifespan,
)


# ----- 请求/响应模型 -----

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default="default")


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


class AgentRequest(BaseModel):
    changelog: str = Field(..., min_length=1)


class AgentResponse(BaseModel):
    status: str
    summary: str
    pr_url: str = ""
    updates: list[dict] = []
    previews: list[str] = []
    details: str = ""


class AgentConfirmRequest(BaseModel):
    confirmed_files: list[str] = Field(..., min_length=1)


class FeedbackRequest(BaseModel):
    session_id: str = "default"
    question: str
    answer: str
    rating: str = Field(..., pattern="^(up|down)$")
    reason: str = ""


class FeedbackResponse(BaseModel):
    status: str


# ----- 接口1: /chat -----

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # 输入护栏
    safe, error_msg = check_input(req.question)
    if not safe:
        raise HTTPException(status_code=400, detail=error_msg)

    # RAG 问答
    qa = get_qa_chat()
    result = qa.ask(req.question, req.session_id)

    # 输出护栏
    safe, safe_answer = check_output(result["answer"])

    return ChatResponse(
        answer=safe_answer,
        sources=result["sources"],
    )


# ----- 接口2: /agent -----

@app.post("/agent", response_model=AgentResponse)
async def agent_run(req: AgentRequest):
    global _pending_updates

    result = run_agent(req.changelog)

    # 暂存待确认的更新
    if result.get("status") == "pending_confirm":
        _pending_updates = result.get("updates", [])

    return AgentResponse(
        status=result.get("status", "error"),
        summary=result.get("summary", ""),
        pr_url=result.get("pr_url", ""),
        updates=result.get("updates", []),
        previews=result.get("previews", []),
        details=result.get("details", ""),
    )


@app.post("/agent/confirm", response_model=AgentResponse)
async def agent_confirm(req: AgentConfirmRequest):
    global _pending_updates

    if not _pending_updates:
        raise HTTPException(status_code=400, detail="没有待确认的更新")

    result = confirm_and_submit(_pending_updates, req.confirmed_files)
    _pending_updates = []

    return AgentResponse(
        status=result.get("status", "error"),
        summary=result.get("summary", ""),
        pr_url=result.get("pr_url", ""),
    )


# ----- 接口3: /feedback -----

@app.post("/feedback", response_model=FeedbackResponse)
async def feedback(req: FeedbackRequest):
    record_feedback(
        session_id=req.session_id,
        question=req.question,
        answer=req.answer,
        rating=req.rating,
        reason=req.reason,
    )
    return FeedbackResponse(status="recorded")


# ----- 健康检查 -----

@app.get("/health")
async def health():
    return {"status": "ok"}