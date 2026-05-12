from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.memory import ConversationSummaryMemory

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from modules.retriever import get_retriever


SYSTEM_PROMPT = """你是技术文档助手，严格基于参考资料回答用户问题。

核心规则：
- 答案必须来源于参考资料，不得编造
- 如果参考资料中找不到相关信息，直接说"未在文档中找到相关内容"，禁止猜测
- 引用文档内容时，注明来源文件名
- 回答简洁准确，使用中文"""

QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", """参考资料：
{context}

用户问题：{question}"""),
])


class QAChat:
    """RAG 问答链，含对话记忆。"""

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            model=LLM_MODEL,
            temperature=0.3,
        )
        self.retriever = get_retriever()
        # session_id → ConversationSummaryMemory
        self._memories: dict[str, ConversationSummaryMemory] = {}

    def _get_memory(self, session_id: str) -> ConversationSummaryMemory:
        if session_id not in self._memories:
            self._memories[session_id] = ConversationSummaryMemory(
                llm=self.llm,
                max_token_limit=200,
                memory_key="history",
                return_messages=True,
            )
        return self._memories[session_id]

    def ask(self, question: str, session_id: str = "default") -> dict:
        # 检索
        results = self.retriever.retrieve(question)
        if not results:
            return {
                "answer": "未在文档中找到相关内容。",
                "sources": [],
            }

        context = "\n\n---\n\n".join(
            f"[来源: {r['filename']}]{r['content']}" for r in results
        )
        sources = list({r["filename"] for r in results})

        # 获取对话记忆
        memory = self._get_memory(session_id)
        history = memory.load_memory_variables({}).get("history", [])

        # 确保 history 是消息列表
        if isinstance(history, str):
            history = [HumanMessage(content=""), AIMessage(content=history)]

        # 生成回答
        chain = QA_PROMPT | self.llm
        response = chain.invoke({
            "context": context,
            "question": question,
            "history": history,
        })

        answer = response.content

        # 保存对话
        memory.save_context(
            {"input": question},
            {"output": answer},
        )

        return {"answer": answer, "sources": sources}


_qa_chat: QAChat | None = None


def get_qa_chat() -> QAChat:
    global _qa_chat
    if _qa_chat is None:
        _qa_chat = QAChat()
    return _qa_chat