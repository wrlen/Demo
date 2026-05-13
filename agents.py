"""
agents.py - 多智能体定义（修复版）
"""
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage
from config import Config
from tools import CustomerServiceTools
from knowledge_base import KnowledgeBase


class OrderAgent:
    """订单专员"""

    def __init__(self):
        self.llm = ChatTongyi(model=Config.MODEL_NAME, temperature=0.1, dashscope_api_key=Config.DASHSCOPE_API_KEY)
        self.tools = CustomerServiceTools()
        self.system_prompt = """你是订单查询专员。用户给了订单号，你必须先用工具查询，再回复。"""

    def process(self, user_input: str) -> dict:
        # 步骤1：提取订单号
        import re, json
        order_id = ""
        match = re.search(r'\d{5,}', user_input)
        if match:
            order_id = match.group()

        # 步骤2：如果有订单号，直接查
        if order_id:
            result = self.tools.query_order(order_id)
            # 步骤3：让LLM润色
            messages = [
                SystemMessage(content="你是订单专员。把查询结果友好地告诉用户。"),
                HumanMessage(content=f"用户问题：{user_input}\n\n查询结果：{result}\n\n请友好回复。")
            ]
            response = self.llm.invoke(messages)
            return {"agent": "order", "result": response.content, "need_transfer": False}
        else:
            # 没订单号，直接回复
            messages = [SystemMessage(content=self.system_prompt), HumanMessage(content=user_input)]
            response = self.llm.invoke(messages)
            return {"agent": "order", "result": response.content, "need_transfer": False}


class AfterSalesAgent:
    """售后专员"""

    def __init__(self):
        self.llm = ChatTongyi(model=Config.MODEL_NAME, temperature=0.2, dashscope_api_key=Config.DASHSCOPE_API_KEY)
        self.tools = CustomerServiceTools()

    def process(self, user_input: str) -> dict:
        import re
        order_id = ""
        match = re.search(r'\d{5,}', user_input)
        if match:
            order_id = match.group()

        tool_results = []
        if order_id:
            # 查订单状态
            tool_results.append(self.tools.query_order(order_id))
            # 查退货资格
            tool_results.append(self.tools.check_return_eligibility(order_id))
            # 如果需要退款金额
            if "退款" in user_input or "退多少" in user_input:
                tool_results.append(self.tools.calculate_refund(order_id))

        if tool_results:
            result_text = "\n".join(tool_results)
            messages = [
                SystemMessage(content="你是售后专员。把查询结果友好地告诉用户，并给出建议。"),
                HumanMessage(content=f"用户问题：{user_input}\n\n查询结果：{result_text}\n\n请友好回复。")
            ]
            response = self.llm.invoke(messages)
            return {"agent": "aftersales", "result": response.content, "need_transfer": False}
        else:
            messages = [
                SystemMessage(content="你是售后专员，回答退货退款问题。直接给出政策说明和建议。"),
                HumanMessage(content=user_input)
            ]
            response = self.llm.invoke(messages)
            return {"agent": "aftersales", "result": response.content, "need_transfer": False}


class KnowledgeAgent:
    """知识专员"""

    def __init__(self):
        self.llm = ChatTongyi(model=Config.MODEL_NAME, temperature=0.3, dashscope_api_key=Config.DASHSCOPE_API_KEY)
        self.kb = KnowledgeBase()
        self.kb.load_existing()
        self.system_prompt = """你是知识专员，回答公司政策、FAQ等问题。

先查看参考政策，基于政策回答。不知道就说不知道，建议联系人工客服。

不要转接，你自己回答知识类问题。"""

    def process(self, user_input: str) -> dict:
        knowledge = self.kb.search(user_input) if self.kb.vector_store else ""
        sp = self.system_prompt + f"\n\n【参考政策】\n{knowledge}"
        messages = [SystemMessage(content=sp), HumanMessage(content=user_input)]
        response = self.llm.invoke(messages)
        return {"agent": "knowledge", "result": response.content, "need_transfer": False}


class SupervisorAgent:
    """主调度"""

    def __init__(self):
        self.llm = ChatTongyi(model=Config.MODEL_NAME, temperature=0.3, dashscope_api_key=Config.DASHSCOPE_API_KEY)
        self.order_agent = OrderAgent()
        self.aftersales_agent = AfterSalesAgent()
        self.knowledge_agent = KnowledgeAgent()
        print("✅ 多智能体系统初始化成功！")
        print("   ├── 📦 订单专员")
        print("   ├── 🔄 售后专员")
        print("   └── 📚 知识专员")

    def process(self, user_input: str) -> str:
        intent = self._classify_intent(user_input)
        print(f"🎯 [调度] 意图: {intent}")

        if intent == "order":
            return self.order_agent.process(user_input)["result"]
        elif intent == "aftersales":
            return self.aftersales_agent.process(user_input)["result"]
        elif intent == "knowledge":
            return self.knowledge_agent.process(user_input)["result"]
        else:
            return self.knowledge_agent.process(user_input)["result"]

    def _classify_intent(self, user_input: str) -> str:
        # 先用关键词快速判断
        if any(w in user_input for w in ["退货", "退款", "换货"]):
            return "aftersales"
        if any(w in user_input for w in ["查", "订单", "物流", "快递", "到哪"]):
            return "order"

        # 关键词判断不了再用 LLM
        messages = [
            SystemMessage(content="分析意图，只回复一个词：order（订单查询）、aftersales（退货退款）、knowledge（政策FAQ）。"),
            HumanMessage(content=user_input)
        ]
        response = self.llm.invoke(messages)
        intent = response.content.strip().lower()
        if "order" in intent:
            return "order"
        elif "after" in intent:
            return "aftersales"
        return "knowledge"