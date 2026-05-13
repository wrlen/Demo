"""
agent_with_tools.py - 完整智能体（支持单Agent和多Agent模式）
================================================================================
【新增功能】
- 多智能体协作模式：Supervisor 调度 + 三个专员分工
- 可在 main.py 中一键切换单/多 Agent 模式
================================================================================
"""

from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config import Config
from knowledge_base import KnowledgeBase
from tools import CustomerServiceToolsV2 as CustomerServiceTools, TOOL_SCHEMAS as TOOL_DESCRIPTIONS
from guard import InputGuard, OutputGuard, ToolPermission
from cache import ResponseCache, ToolResultCache
from logger import ChatLogger
from agents import SupervisorAgent  # 🆕 多智能体
import json
import re
import time


class AgentWithTools:
    """完整智能体 - 支持单Agent和多Agent两种模式"""

    def __init__(self, use_multi_agent: bool = True):
        """
        初始化智能体

        参数:
            use_multi_agent: True=多智能体协作, False=单智能体
        """
        # ===== LLM（大脑） =====
        self.llm = ChatTongyi(
            model=Config.MODEL_NAME,
            temperature=Config.TEMPERATURE,
            dashscope_api_key=Config.DASHSCOPE_API_KEY
        )

        # ===== 知识库 =====
        self.kb = KnowledgeBase()
        kb_loaded = self.kb.load_existing()
        if not kb_loaded:
            print("⚠️  警告：知识库未加载")

        # ===== 工具集 =====
        self.tools = CustomerServiceTools()

        # ===== 对话历史 =====
        self.conversation_history = []

        # ===== 缓存 =====
        self.response_cache = ResponseCache(ttl_seconds=600)
        self.tool_cache = ToolResultCache(ttl_seconds=60)

        # ===== 日志 =====
        self.logger = ChatLogger()

        # ===== 🆕 多智能体系统 =====
        self.use_multi_agent = use_multi_agent
        if use_multi_agent:
            self.supervisor = SupervisorAgent()

        print("✅ 完整智能体初始化成功！")
        print(f"   - LLM: {Config.MODEL_NAME}")
        print(f"   - 知识库: {'已加载' if kb_loaded else '未加载'}")
        print(f"   - 工具集: {self.tools.get_order_count()} 条订单数据")
        print(f"   - 安全防护: 🛡️ 已启用")
        print(f"   - 模式: {'🌐 多智能体协作' if use_multi_agent else '🤖 单智能体'}")

    # ========================================================================
    # 主入口
    # ========================================================================

    def chat(self, user_input: str) -> str:
        """
        智能对话主入口
        根据模式选择单Agent或多Agent路径
        """
        # 🆕 多智能体模式
        if self.use_multi_agent:
            return self._chat_multi_agent(user_input)

        # 单Agent模式（原有逻辑）
        return self._chat_single_agent(user_input)

    # ========================================================================
    # 🆕 多智能体路径
    # ========================================================================

    def _chat_multi_agent(self, user_input: str) -> str:
        """多智能体协作路径"""
        start_time = time.time()

        # 🛡️ 输入过滤
        is_safe, reason = InputGuard.check(user_input)
        if not is_safe:
            print(f"🛡️ [输入拦截] {reason}")
            return f"⚠️ {reason}"

        # ⚡ 缓存检查
        cached_response = self.response_cache.get(user_input)
        if cached_response:
            return cached_response

        # 🌐 多智能体处理
        response = self.supervisor.process(user_input)

        # 🛡️ 输出审核
        response = OutputGuard.sanitize(response)
        is_safe, reason = OutputGuard.check(response)
        if not is_safe:
            print(f"🛡️ [输出拦截] {reason}")
            response = "抱歉，我无法提供该信息。请联系人工客服。"

        # ⚡ 存入缓存
        self.response_cache.set(user_input, response)

        # 📝 日志
        response_time = int((time.time() - start_time) * 1000)
        self.logger.log(user_input, response, response_time_ms=response_time)

        # 更新对话历史
        self.conversation_history.append(HumanMessage(content=user_input))
        self.conversation_history.append(AIMessage(content=response))

        return response

    # ========================================================================
    # 单Agent路径（原有逻辑）
    # ========================================================================

    def _chat_single_agent(self, user_input: str) -> str:
        """单Agent路径"""
        start_time = time.time()

        # 🛡️ 输入过滤
        is_safe, reason = InputGuard.check(user_input)
        if not is_safe:
            return f"⚠️ {reason}"

        # ⚡ 缓存检查
        cached_response = self.response_cache.get(user_input)
        if cached_response:
            return cached_response

        # RAG 检索
        knowledge_context = self.kb.search(user_input) if self.kb.vector_store else ""

        # 意图判断
        needs_tool = self._needs_tool(user_input)

        if needs_tool:
            response = self._chat_with_tools(user_input, knowledge_context)
        else:
            response = self._chat_with_knowledge(user_input, knowledge_context)

        # 🛡️ 输出审核
        response = OutputGuard.sanitize(response)
        is_safe, reason = OutputGuard.check(response)
        if not is_safe:
            response = "抱歉，我无法提供该信息。请联系人工客服。"

        # ⚡ 存入缓存
        self.response_cache.set(user_input, response)

        # 📝 日志
        response_time = int((time.time() - start_time) * 1000)
        self.logger.log(user_input, response, response_time_ms=response_time)

        return response

    # ========================================================================
    # 意图判断
    # ========================================================================

    def _needs_tool(self, user_input: str) -> bool:
        """判断是否需要调用工具"""
        if re.search(r'\d{5,}', user_input):
            return True
        tool_keywords = ['查询订单', '退货', '退款', '换货', '物流', '快递', '订单', '查下', '查一下']
        return any(keyword in user_input for keyword in tool_keywords)

    # ========================================================================
    # 工具调用路径
    # ========================================================================

    def _chat_with_tools(self, user_input: str, knowledge_context: str) -> str:
        """工具调用路径"""

        # ① LLM 选择工具
        tool_selection_prompt = f"""你需要帮助用户处理问题。

用户问题：{user_input}

可用工具：
{TOOL_DESCRIPTIONS}

请用JSON格式回复：
{{"tool": "工具名", "params": {{"order_id": "订单号"}}}}
不需要工具回复：{{"tool": "none"}}
只回复JSON。"""

        messages = [
            SystemMessage(content="你是工具调用决策助手。只返回JSON。"),
            HumanMessage(content=tool_selection_prompt)
        ]

        response = self.llm.invoke(messages)
        response_text = response.content.strip()

        # ② 解析 JSON
        try:
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            tool_call = json.loads(response_text)
        except json.JSONDecodeError:
            return self._chat_with_knowledge(user_input, knowledge_context)

        if tool_call.get('tool') == 'none':
            return self._chat_with_knowledge(user_input, knowledge_context)

        tool_name = tool_call.get('tool', '')
        params = tool_call.get('params', {})

        print(f"🔧 [工具调用] 工具={tool_name}, 参数={params}")

        # ③ 权限检查
        allowed, msg = ToolPermission.check_tool_permission(tool_name, params)
        if not allowed:
            return f"⚠️ 操作被限制：{msg}，请联系人工客服"

        # ④ 执行工具
        try:
            if tool_name == 'query_order':
                tool_result = self.tools.query_order(params.get('order_id', ''))
            elif tool_name == 'check_return_eligibility':
                tool_result = self.tools.check_return_eligibility(params.get('order_id', ''))
            elif tool_name == 'calculate_refund_amount':
                tool_result = self.tools.calculate_refund_amount(params.get('order_id', ''))
            elif tool_name == 'calculate_refund': result = self.tools.calculate_refund(
                params.get('order_id', ''))
            tool_result = f"未知工具: {tool_name}"
            print(f"✅ [工具结果] {tool_result[:100]}...")
        except Exception as e:
            tool_result = f"工具执行出错: {str(e)}"

        # ⑤ 生成回复
        final_prompt = f"""你是客服助手小智。

用户问题：{user_input}

工具查询结果：
{tool_result}

相关政策：
{knowledge_context}

要求：友好回复，不要编造，不要承诺。"""

        final_messages = [
            SystemMessage(content=final_prompt),
            HumanMessage(content="请生成回复")
        ]

        final_response = self.llm.invoke(final_messages)

        self.conversation_history.append(HumanMessage(content=user_input))
        self.conversation_history.append(AIMessage(content=final_response.content))

        return final_response.content

    # ========================================================================
    # 知识库路径
    # ========================================================================

    def _chat_with_knowledge(self, user_input: str, knowledge_context: str) -> str:
        """知识库路径"""

        system_prompt = Config.SYSTEM_PROMPT + f"""

【参考政策】
{knowledge_context}

要求：基于政策回答，不要编造，不要承诺。"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input)
        ]

        response = self.llm.invoke(messages)

        self.conversation_history.append(HumanMessage(content=user_input))
        self.conversation_history.append(AIMessage(content=response.content))

        return response.content

    # ========================================================================
    # 流式输出
    # ========================================================================

    def chat_stream(self, user_input: str):
        """流式输出"""
        from dashscope import Generation

        is_safe, reason = InputGuard.check(user_input)
        if not is_safe:
            yield f"⚠️ {reason}"
            return

        cached_response = self.response_cache.get(user_input)
        if cached_response:
            yield cached_response
            return

        knowledge_context = self.kb.search(user_input) if self.kb.vector_store else ""

        messages = [{"role": "system", "content": Config.SYSTEM_PROMPT}]
        if knowledge_context:
            messages[0]["content"] += f"\n\n【参考政策】\n{knowledge_context}"

        history = self.conversation_history[-Config.MAX_HISTORY * 2:] if len(
            self.conversation_history) > Config.MAX_HISTORY * 2 else self.conversation_history
        for msg in history:
            if hasattr(msg, 'type'):
                if msg.type == "human":
                    messages.append({"role": "user", "content": msg.content})
                elif msg.type == "ai":
                    messages.append({"role": "assistant", "content": msg.content})

        messages.append({"role": "user", "content": user_input})

        full_response = ""
        try:
            responses = Generation.call(
                model=Config.MODEL_NAME,
                messages=messages,
                result_format='message',
                stream=True,
                incremental_output=True,
                api_key=Config.DASHSCOPE_API_KEY
            )

            for response in responses:
                if response.status_code == 200:
                    chunk = response.output.choices[0].message.content
                    full_response += chunk
                    yield chunk
        except Exception as e:
            yield f"\n[出错: {str(e)}]"
            return

        full_response = OutputGuard.sanitize(full_response)
        self.response_cache.set(user_input, full_response)

        self.conversation_history.append(HumanMessage(content=user_input))
        self.conversation_history.append(AIMessage(content=full_response))


# ============================================================================
# 测试
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 完整智能客服系统测试")
    print("=" * 60)

    # 默认使用多Agent模式
    agent = AgentWithTools(use_multi_agent=True)

    print("\n💡 试试: 帮我查下订单12345")
    print("💡 试试: 订单12345可以退款吗？")
    print("💡 试试: 你们的保修政策是什么？")
    print("\n输入 'quit' 退出\n")

    while True:
        try:
            user_input = input("\n👤 你: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("再见！")
                break
            if not user_input:
                continue

            print("\n🤖 小智: ", end="")
            response = agent.chat(user_input)
            print(response)
            print("\n" + "-" * 60)
        except KeyboardInterrupt:
            print("\n\n再见！")
            break