"""
agent_v2.py - 精简版智能体
直接让 LLM 判断意图 → 执行工具 → 润色回复
不依赖 API 原生 Function Calling
================================================================================
"""

from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage
from config import Config
from tools import CustomerServiceToolsV2
from guard import InputGuard, OutputGuard
from cache import ResponseCache
import re


class AgentV2:
    """智能体 V2 - 规则判断 + LLM 润色"""

    def __init__(self):
        self.llm = ChatTongyi(
            model=Config.MODEL_NAME,
            temperature=0.3,
            dashscope_api_key=Config.DASHSCOPE_API_KEY
        )
        self.tools = CustomerServiceToolsV2()
        self.response_cache = ResponseCache(ttl_seconds=600)

        # 关键词 → 工具映射
        self.keyword_tool_map = {
            "退款": "calculate_refund",
            "退货": "check_return_eligibility",
            "换货": "check_return_eligibility",
        }

        print("✅ Agent V2 初始化成功！")

    def chat(self, user_input: str) -> str:
        """对话主入口"""

        # 🛡️ 输入过滤
        is_safe, reason = InputGuard.check(user_input)
        if not is_safe:
            return f"⚠️ {reason}"

        # ⚡ 缓存
        cached = self.response_cache.get(user_input)
        if cached:
            return cached

        # ===== ① 提取订单号 =====
        order_id = self._extract_order_id(user_input)

        # ===== ② 判断意图 → 执行工具 =====
        tool_result = self._execute_tool(user_input, order_id)

        # ===== ③ LLM 润色 =====
        if tool_result:
            answer = self._polish(user_input, tool_result)
        else:
            answer = self._direct_answer(user_input)

        # 🛡️ 输出审核
        answer = OutputGuard.sanitize(answer)
        self.response_cache.set(user_input, answer)
        return answer

    def _extract_order_id(self, user_input: str) -> str:
        """提取订单号"""
        match = re.search(r'\d{5,}', user_input)
        return match.group() if match else ""

    def _execute_tool(self, user_input: str, order_id: str) -> str:
        """根据关键词执行工具"""
        if not order_id:
            return ""

        # 先查订单基本信息
        result = self.tools.query_order(order_id)

        # 如果有退货退款关键词，追加相关信息
        if "退款" in user_input:
            refund = self.tools.calculate_refund(order_id)
            result += "\n" + refund

        if "退货" in user_input or "退款" in user_input or "换货" in user_input:
            eligibility = self.tools.check_return_eligibility(order_id)
            result += "\n" + eligibility

        return result

    def _polish(self, user_input: str, tool_result: str) -> str:
        """让 LLM 把工具结果润色成友好回复"""
        messages = [
            SystemMessage(content="""你是客服小智。把查询结果用友好、自然的语言回复用户。

要求：
1. 语气亲切
2. 关键信息（订单号、商品、状态、金额）要清晰
3. 不编造信息"""),
            HumanMessage(content=f"用户问题：{user_input}\n\n查询结果：{tool_result}\n\n请生成友好回复。")
        ]

        response = self.llm.invoke(messages)
        content = response.content.strip()

        # 如果 LLM 返回空，直接用工具结果
        return content if content else f"查询结果：{tool_result}"

    def _direct_answer(self, user_input: str) -> str:
        """无工具时的直接回答"""
        messages = [
            SystemMessage(content=Config.SYSTEM_PROMPT),
            HumanMessage(content=user_input)
        ]
        response = self.llm.invoke(messages)
        return response.content


# ============================================================================
# 测试
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 Agent V2 测试")
    print("=" * 60)

    agent = AgentV2()

    tests = [
        "帮我查下订单12345",
        "订单12345可以退款吗？",
        "订单67890退款多少钱？",
        "你们的保修政策是什么？",
    ]

    for q in tests:
        print(f"\n{'=' * 60}")
        print(f"👤 {q}")
        print(f"{'=' * 60}")
        print(f"🤖 {agent.chat(q)}")