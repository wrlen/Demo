"""
agent_core.py - 基础智能体（最简可用版本）
================================================================================
【核心概念】什么是 Agent（智能体）？

一个最基础的智能体 = LLM（大脑）+ 对话记忆（短期记忆）

它能做到：
- 理解用户意图
- 记住刚刚说过的话
- 用自然语言友好回复

它还不能做到：
- 查数据库
- 读公司文档
- 执行具体操作

这些高级能力在 agent_with_tools.py 中实现。
================================================================================
"""

# ============================================================================
# 导入依赖
# ============================================================================

# ChatTongyi：通义千问的 LangChain 适配器
# 它把通义千问的 API 包装成 LangChain 统一接口
# 好处：以后换模型（如换成 OpenAI），只需改这一行，其他地方不用动
from langchain_community.chat_models import ChatTongyi

# 消息类型：LangChain 用不同类区分消息角色
# SystemMessage：系统指令（设定 AI 的人设和规则）
# HumanMessage：用户说的话
# AIMessage：AI 的回复
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from config import Config
from typing import List, Dict


class CustomerServiceAgent:
    """
    基础智能客服类

    【工作原理】
    每次用户说话时：
    1. 拿出"系统提示词"（告诉 AI 它是谁）
    2. 拿出"最近对话历史"（让 AI 知道刚才聊了什么）
    3. 加上"用户刚说的话"
    4. 一起发给 LLM
    5. LLM 返回回复
    6. 保存这轮对话到历史（下次用）

    【类比】
    就像一个记性有限的客服人员：
    - 他手里有一本"工作手册"（系统提示词）
    - 他记得最近10轮的对话（对话历史）
    - 每次回答问题前，他会翻看最近聊了什么
    - 但他不记得10轮以前的事（存储器有限）
    """

    def __init__(self):
        """
        初始化智能体

        做了什么：
        1. 创建 LLM 连接（打通义千问的"电话线"）
        2. 准备空的对话历史（"笔记本"）
        3. 准备空的用户记忆（"客户档案"）
        """
        # ===== 1. 初始化 LLM（大脑） =====
        # ChatTongyi 把通义千问 API 包装了一下
        # 我们只需要传配置，它会自动处理 HTTP 请求、重试等复杂逻辑
        self.llm = ChatTongyi(
            model=Config.MODEL_NAME,  # 用哪个模型（qwen-turbo）
            temperature=Config.TEMPERATURE,  # 回复的稳定程度（0.3）
            dashscope_api_key=Config.DASHSCOPE_API_KEY  # 身份凭证
        )

        # ===== 2. 对话历史（短期记忆） =====
        # 存储最近的对话，每条是 HumanMessage 或 AIMessage
        # 为什么是 List？按时间顺序排列，最新的在后面
        self.conversation_history: List = []

        # ===== 3. 用户信息记忆（长期记忆） =====
        # 存储用户的基本信息，比如姓名、偏好
        # 实际项目中这里可能是数据库
        self.user_memory: Dict = {}

        print("✅ 智能体初始化成功！（通义千问）")

    def chat(self, user_input: str) -> str:
        """
        处理用户输入，返回 AI 回复

        【详细流程】
        ① 准备系统提示词（AI 的人设）
        ② 取出最近的对话历史（但不超过 MAX_HISTORY 轮）
        ③ 加上用户刚说的话
        ④ 打包发给 LLM
        ⑤ 把 LLM 回复保存到历史

        参数:
            user_input: 用户输入的文字

        返回:
            AI 的回复文字
        """
        # ===== 步骤①：准备系统提示词 =====
        # SystemMessage 告诉 AI："你是客服小智，你的职责是..."
        messages = [SystemMessage(content=Config.SYSTEM_PROMPT)]

        # ===== 步骤②：添加对话历史 =====
        # 为什么要限制历史长度？
        # LLM 有"上下文窗口"限制，一次只能处理有限文本
        # 历史太长 → 超出限制 → 报错
        # 历史太长 → token 消耗多 → 烧钱
        max_messages = Config.MAX_HISTORY * 2  # 每轮有用户和AI两条，所以要×2
        if len(self.conversation_history) > max_messages:
            # 只保留最近的，旧的"忘记"
            self.conversation_history = self.conversation_history[-max_messages:]
        messages.extend(self.conversation_history)

        # ===== 步骤③：添加当前用户问题 =====
        messages.append(HumanMessage(content=user_input))

        # ===== 步骤④：调用 LLM =====
        # invoke() 把消息发给通义千问，等待回复
        # 这是同步调用（程序会等在这里，直到收到回复）
        # 实际项目中可以用异步调用提高并发性能
        response = self.llm.invoke(messages)

        # ===== 步骤⑤：保存到历史 =====
        # 把用户的话和 AI 的回复都存起来，下次对话时带上
        self.conversation_history.append(HumanMessage(content=user_input))
        self.conversation_history.append(AIMessage(content=response.content))

        return response.content


# ============================================================================
# 命令行测试入口
# 直接运行 python agent_core.py 可以测试基础对话
# ============================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 基础智能客服测试")
    print("=" * 50)

    agent = CustomerServiceAgent()

    print("\n开始对话（输入 'quit' 退出）\n")

    while True:
        try:
            user_input = input("\n👤 你: ").strip()
            if user_input.lower() == 'quit':
                print("再见！")
                break
            if not user_input:
                continue

            response = agent.chat(user_input)
            print(f"\n🤖 小智: {response}")
        except KeyboardInterrupt:
            print("\n\n再见！")
            break