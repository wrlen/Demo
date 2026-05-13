from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from modules.retriever import get_retriever
from modules.quality import get_optimizer
from modules.cache import cache_qa, get_cache_stats, clear_all_cache


SYSTEM_PROMPT = """你是技术文档助手，严格基于参考资料回答用户问题。

核心规则：
- 答案必须来源于参考资料，不得编造
- 如果参考资料中找不到相关信息，直接说"未在文档中找到相关内容"，禁止猜测
- 引用文档内容时，注明来源文件名
- 回答简洁准确，使用中文
- 理解对话上下文，可以引用之前的对话内容"""

QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", """参考资料：
{context}

用户问题：{question}"""),
])

SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是一个对话摘要助手。请将以下对话历史摘要成一段简洁的文字，保留关键信息和上下文。"),
    ("human", "{dialogue}"),
])


class EnhancedMemory:
    """增强的对话记忆，支持摘要和更长的对话历史。"""

    def __init__(self, max_turns: int = 5, summary_threshold: int = 3):
        self.max_turns = max_turns
        self.summary_threshold = summary_threshold
        self.messages: list = []
        self.summary: str = ""
        self.llm = ChatOpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            model=LLM_MODEL,
            temperature=0.1,
        )

    def add_message(self, question: str, answer: str):
        self.messages.append(HumanMessage(content=question))
        self.messages.append(AIMessage(content=answer))
        
        # 当达到摘要阈值时，生成摘要
        if len(self.messages) >= self.summary_threshold * 2:
            self._update_summary()
        
        # 保留最近 max_turns 轮
        if len(self.messages) > self.max_turns * 2:
            self.messages = self.messages[-self.max_turns * 2:]

    def _update_summary(self):
        """生成对话摘要"""
        dialogue = "\n".join([
            f"用户: {m.content}" if isinstance(m, HumanMessage) else f"助手: {m.content}"
            for m in self.messages[:-2]  # 不包含最新一轮
        ])
        
        if dialogue:
            chain = SUMMARY_PROMPT | self.llm
            response = chain.invoke({"dialogue": dialogue})
            self.summary = response.content

    def load_messages(self) -> list:
        """加载对话历史，包含摘要"""
        history = []
        if self.summary:
            history.append(SystemMessage(content=f"对话摘要：{self.summary}"))
        history.extend(self.messages)
        return history

    def clear(self):
        """清空对话记忆"""
        self.messages = []
        self.summary = ""


class IntentRecognizer:
    """意图识别器"""
    
    INTENT_TEMPLATES = {
        "summary": ["总结", "概括", "回顾", "小结"],
        "example": ["举例", "例子", "示例"],
        "clarify": ["什么是", "解释", "说明", "定义"],
        "compare": ["比较", "对比", "区别"],
        "howto": ["如何", "怎么", "步骤", "教程"],
        "troubleshoot": ["错误", "问题", "故障", "报错"],
        "refine": ["详细", "具体", "更多", "深入"],
    }

    @classmethod
    def recognize(cls, question: str) -> str:
        """识别用户意图"""
        question_lower = question.lower()
        
        for intent, keywords in cls.INTENT_TEMPLATES.items():
            for keyword in keywords:
                if keyword in question_lower:
                    return intent
        
        return "general"


class QAChat:
    """RAG 问答链，含增强对话记忆和质量评估。"""

    def __init__(self, enable_quality_check: bool = True):
        self.llm = ChatOpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            model=LLM_MODEL,
            temperature=0.3,
        )
        self.retriever = get_retriever()
        self.optimizer = get_optimizer()
        self.enable_quality_check = enable_quality_check
        # session_id → EnhancedMemory
        self._memories: dict[str, EnhancedMemory] = {}

    def _get_memory(self, session_id: str) -> EnhancedMemory:
        if session_id not in self._memories:
            self._memories[session_id] = EnhancedMemory(max_turns=5)
        return self._memories[session_id]

    @cache_qa
    def ask(self, question: str, session_id: str = "default") -> dict:
        # 识别意图
        intent = IntentRecognizer.recognize(question)
        
        # 检索
        results = self.retriever.retrieve(question)
        if not results:
            return {
                "answer": "未在文档中找到相关内容。",
                "sources": [],
                "intent": intent,
                "quality_score": 0,
                "optimized": False,
            }

        context = "\n\n---\n\n".join(
            f"[来源：{r['filename']}]{r['content']}" for r in results
        )
        sources = list({r["filename"] for r in results})

        # 获取对话记忆
        memory = self._get_memory(session_id)
        history = memory.load_messages()

        # 生成回答
        chain = QA_PROMPT | self.llm
        response = chain.invoke({
            "context": context,
            "question": question,
            "history": history,
        })

        answer = response.content
        quality_score = 100
        optimized = False

        # 质量评估与优化
        if self.enable_quality_check:
            optimization_result = self.optimizer.optimize(context, question, answer)
            answer = optimization_result["answer"]
            quality_score = optimization_result["original_score"]
            optimized = optimization_result["optimized"]

        # 保存对话（保存优化后的回答）
        memory.add_message(question, answer)

        return {
            "answer": answer,
            "sources": sources,
            "intent": intent,
            "quality_score": quality_score,
            "optimized": optimized,
        }

    def clear_history(self, session_id: str):
        """清空指定会话的对话历史"""
        if session_id in self._memories:
            self._memories[session_id].clear()


_qa_chat: QAChat | None = None


def get_qa_chat() -> QAChat:
    global _qa_chat
    if _qa_chat is None:
        _qa_chat = QAChat()
    return _qa_chat