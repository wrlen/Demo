import os
import ssl

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
ssl._create_default_https_context = ssl._create_unverified_context

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from modules import logger
from modules.qa import get_qa_chat
from modules.agent import run_agent, confirm_and_submit
from modules.guard import check_input, check_output, record_feedback

# ----- 全局状态 -----
# 使用 session_id 隔离用户状态
_pending_updates: dict[str, list[dict]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭时的生命周期管理。"""
    logger.info("应用启动中...")
    # 预热检索器
    try:
        get_qa_chat()
        logger.info("问答模块已就绪")
    except Exception as e:
        logger.warning(f"检索器初始化警告: {e}")
    yield
    logger.info("应用关闭")


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
    session_id: str = Field(default="default")


class AgentResponse(BaseModel):
    status: str
    summary: str
    pr_url: str = ""
    updates: list[dict] = []
    previews: list[str] = []
    details: str = ""


class AgentConfirmRequest(BaseModel):
    confirmed_files: list[str] = Field(..., min_length=1)
    session_id: str = Field(default="default")


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
    logger.info(f"问答请求: session_id={req.session_id}")

    # 输入护栏
    safe, error_msg = check_input(req.question)
    if not safe:
        logger.warning(f"输入护栏拦截: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

    # RAG 问答
    qa = get_qa_chat()
    result = qa.ask(req.question, req.session_id)

    # 输出护栏
    safe, safe_answer = check_output(result["answer"])
    if not safe:
        logger.warning("输出护栏拦截了潜在不安全的回答")

    logger.info(f"问答完成: 来源数={len(result['sources'])}")
    return ChatResponse(
        answer=safe_answer,
        sources=result["sources"],
    )


# ----- 接口2: /agent -----

@app.post("/agent", response_model=AgentResponse)
async def agent_run(req: AgentRequest):
    session_id = req.session_id
    logger.info(f"Agent 执行请求: session_id={session_id}")

    result = run_agent(req.changelog)

    # 暂存待确认的更新，按 session_id 隔离
    if result.get("status") == "pending_confirm":
        _pending_updates[session_id] = result.get("updates", [])
        logger.info(f"更新预览已保存: session_id={session_id}, 文档数={len(result.get('updates', []))}")
    elif result.get("status") == "error":
        logger.error(f"Agent 执行失败: {result.get('summary')}")

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
    session_id = req.session_id
    pending = _pending_updates.get(session_id, [])

    if not pending:
        logger.warning(f"没有找到待确认的更新: session_id={session_id}")
        raise HTTPException(status_code=400, detail="没有待确认的更新")

    logger.info(f"提交变更确认: session_id={session_id}, 文件={req.confirmed_files}")
    result = confirm_and_submit(pending, req.confirmed_files)

    # 清理已处理的更新
    if session_id in _pending_updates:
        del _pending_updates[session_id]

    if result.get("status") == "success":
        logger.info(f"变更提交成功: {result.get('summary')}")
    else:
        logger.error(f"变更提交失败: {result.get('summary')}")

    return AgentResponse(
        status=result.get("status", "error"),
        summary=result.get("summary", ""),
        pr_url=result.get("pr_url", ""),
    )


# ----- 接口3: /feedback -----

@app.post("/feedback", response_model=FeedbackResponse)
async def feedback(req: FeedbackRequest):
    logger.info(f"收到用户反馈: rating={req.rating}, session_id={req.session_id}")
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


# ----- 接口4: /documents - 文档管理 -----

from fastapi import File, UploadFile
from typing import List

class DocumentResponse(BaseModel):
    name: str
    size: int
    updated_at: str

class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]

@app.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """获取文档列表"""
    docs_dir = os.path.join(os.path.dirname(__file__), 'data', 'docs')
    documents = []
    
    if os.path.exists(docs_dir):
        for filename in sorted(os.listdir(docs_dir)):
            if filename.endswith('.md'):
                filepath = os.path.join(docs_dir, filename)
                filesize = os.path.getsize(filepath)
                mtime = os.path.getmtime(filepath)
                updated_at = f"{mtime}"  # Unix timestamp for simplicity
                documents.append({
                    "name": filename,
                    "size": filesize,
                    "updated_at": updated_at
                })
    
    logger.info(f"获取文档列表: {len(documents)} 个文档")
    return DocumentListResponse(documents=documents)


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档"""
    if not file.filename.endswith('.md'):
        raise HTTPException(status_code=400, detail="只支持 Markdown 文件 (.md)")
    
    docs_dir = os.path.join(os.path.dirname(__file__), 'data', 'docs')
    os.makedirs(docs_dir, exist_ok=True)
    
    filepath = os.path.join(docs_dir, file.filename)
    
    # 检查文件是否已存在
    if os.path.exists(filepath):
        raise HTTPException(status_code=409, detail=f"文件 {file.filename} 已存在")
    
    try:
        contents = await file.read()
        with open(filepath, 'wb') as f:
            f.write(contents)
        
        logger.info(f"文档上传成功: {file.filename}")
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """删除文档"""
    if not filename.endswith('.md'):
        raise HTTPException(status_code=400, detail="只支持删除 Markdown 文件")
    
    docs_dir = os.path.join(os.path.dirname(__file__), 'data', 'docs')
    filepath = os.path.join(docs_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")
    
    try:
        os.remove(filepath)
        logger.info(f"文档删除成功: {filename}")
        return {"status": "success", "filename": filename}
    except Exception as e:
        logger.error(f"文档删除失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@app.post("/documents/rebuild")
async def rebuild_index():
    """重建文档索引"""
    try:
        from modules.retriever import rebuild_index
        rebuild_index()
        logger.info("文档索引重建成功")
        return {"status": "success", "message": "索引重建完成"}
    except Exception as e:
        logger.error(f"索引重建失败: {e}")
        raise HTTPException(status_code=500, detail=f"索引重建失败: {str(e)}")


@app.get("/search")
async def search_documents(query: str, limit: int = 5):
    """全文搜索文档"""
    if not query:
        raise HTTPException(status_code=400, detail="搜索关键词不能为空")
    
    try:
        from modules.cache import cache_search
        from modules.retriever import get_retriever
        
        @cache_search
        def cached_search(q: str, top_k: int):
            retriever = get_retriever()
            return retriever.retrieve(q, top_k=top_k)
        
        results = cached_search(query, limit)
        
        search_results = []
        for result in results:
            search_results.append({
                "filename": result.get("filename", ""),
                "content": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                "score": result.get("score", 0)
            })
        
        logger.info(f"搜索完成: query={query}, 结果数={len(search_results)}")
        return {"results": search_results, "total": len(search_results)}
    
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


# ----- 接口5: /cache - 缓存管理 -----

@app.get("/cache/stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    try:
        from modules.cache import get_cache_stats as get_stats
        stats = get_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")


@app.post("/cache/clear")
async def clear_cache():
    """清空所有缓存"""
    try:
        from modules.cache import clear_all_cache
        clear_all_cache()
        logger.info("缓存已清空")
        return {"status": "success", "message": "缓存已清空"}
    except Exception as e:
        logger.error(f"清空缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空缓存失败: {str(e)}")


# ----- 测试端点 -----

@app.get("/test_qa")
async def test_qa():
    """测试问答功能的端点"""
    try:
        qa = get_qa_chat()
        result = qa.ask("如何配置数据库？", "test")
        return {"status": "success", "result": result}
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


# ----- 原始搜索接口保留（用于对比测试）-----

@app.get("/search/original")
async def search_documents_original(query: str, limit: int = 5):
    """全文搜索文档（无缓存）"""
    if not query:
        raise HTTPException(status_code=400, detail="搜索关键词不能为空")
    
    try:
        from modules.retriever import get_retriever
        retriever = get_retriever()
        results = retriever.retrieve(query, top_k=limit)
        
        search_results = []
        for result in results:
            search_results.append({
                "filename": result.get("filename", ""),
                "content": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                "score": result.get("score", 0)
            })
        
        logger.info(f"搜索完成: query={query}, 结果数={len(search_results)}")
        return {"results": search_results, "total": len(search_results)}
    
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")