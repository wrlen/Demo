"""
main.py - Streamlit Web 界面
================================================================================
【为什么用 Streamlit？】
- 纯 Python 代码就能创建 Web 应用，不需要学 HTML/CSS/JS
- 内置聊天组件 st.chat_message / st.chat_input
- 适合快速原型开发，10 分钟就能搭好界面
- 支持实时刷新、会话状态管理

【启动方式】
在终端执行：streamlit run main.py
浏览器自动打开：http://localhost:8501
================================================================================
"""

import streamlit as st
from agent_with_tools import AgentWithTools
from knowledge_base import KnowledgeBase
from logger import ChatLogger  #  新增导入
import pandas as pd           #  用于数据展示

# ============================================================================
# 页面基础配置
# ============================================================================
st.set_page_config(
    page_title="极客科技智能客服",  # 浏览器标签页上显示的文字
    page_icon="🤖",  # 标签页上的图标
    layout="centered",  # 页面内容居中（也可以选 "wide"）
    initial_sidebar_state="expanded"  # 侧边栏默认展开
)

# ============================================================================
# 应用标题
# ============================================================================
st.title("🤖 极客科技智能客服")
st.caption("我是小智，很高兴为您服务！")

# ============================================================================
# 初始化会话状态
# ============================================================================
# st.session_state 是 Streamlit 的"全局变量"
# 页面刷新、重新运行时，里面的数据不会丢失
# 这是保持聊天记录的关键！

if 'agent' not in st.session_state:
    # 第一次运行时初始化智能体
    st.session_state.agent = AgentWithTools(use_multi_agent=True)
    # 用一个列表存储所有聊天记录
    st.session_state.messages = []
    st.session_state.logger = ChatLogger()  # 🆕 初始化日志器
    st.session_state.use_multi_agent = True  # 🆕 控制统计面板显示

# ============================================================================
# 侧边栏 - 系统管理和快捷操作
# ============================================================================
with st.sidebar:
    st.header("⚙️ 系统管理")
    st.subheader("🤖 智能体模式")

    # 模式切换按钮
    if 'use_multi_agent' not in st.session_state:
        st.session_state.use_multi_agent = True

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌐 多Agent",
                     use_container_width=True,
                     type="primary" if st.session_state.use_multi_agent else "secondary"):
            st.session_state.use_multi_agent = True
            st.session_state.agent = AgentWithTools(use_multi_agent=True)
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🤖 单Agent",
                     use_container_width=True,
                     type="primary" if not st.session_state.use_multi_agent else "secondary"):
            st.session_state.use_multi_agent = False
            st.session_state.agent = AgentWithTools(use_multi_agent=False)
            st.session_state.messages = []
            st.rerun()

    st.caption(f"当前: {'🌐 多智能体协作' if st.session_state.use_multi_agent else '🤖 单智能体模式'}")

    # --- 知识库管理 ---
    st.subheader("📚 知识库")
    if st.button("🔄 重建知识库", use_container_width=True):
        with st.spinner("正在重建知识库..."):
            kb = KnowledgeBase()
            kb.load_documents("data/company_policy.txt")
            # 重建后要重新初始化智能体，让它加载新的知识库
            st.session_state.agent = AgentWithTools()
            st.success("✅ 知识库重建成功！")
            st.rerun()

    # --- 清除对话 ---
    if st.button("🗑️ 清除对话", use_container_width=True):
        st.session_state.messages = []
        st.session_state.agent.conversation_history = []
        st.rerun()

    st.divider()

    # --- 快速测试问题 ---
    st.subheader("💡 试试这些问题")

    demo_questions = [
        "帮我查下订单12345",
        "如何退货？",
        "订单12345可以退款吗？",
        "你们的保修政策是什么？",
        "可以修改收货地址吗？",
        "如何开发票？"
    ]

    # 点击按钮直接模拟用户提问
    for q in demo_questions:
        if st.button(q, key=f"demo_{q}", use_container_width=True):
            # 模拟用户发送消息
            st.session_state.messages.append({"role": "user", "content": q})
            # 获取智能体回复
            with st.spinner("思考中..."):
                response = st.session_state.agent.chat(q)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

    st.divider()

    # --- 系统状态 ---
    st.subheader("📊 系统状态")
    st.write(f"💬 对话轮数: {len(st.session_state.messages) // 2}")

    # 检查知识库是否加载
    if st.session_state.agent.kb.vector_store:
        st.write("📚 知识库: ✅ 已加载")
    else:
        st.write("📚 知识库: ❌ 未加载")

    st.write(f"🔧 工具集: {(st.session_state.agent.tools.get_order_count())} 条订单")
    st.divider()
    # 🆕 ===== 日志统计面板 =====
    # --- 运营数据 ---
    st.subheader("📈 运营数据")
    if st.button("🔄 刷新统计", use_container_width=True):
        st.rerun()

    # ✅ 用智能体自带的 logger
    log = st.session_state.agent.logger
    stats = log.get_stats()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📝 总对话", stats["总对话数"])
    with col2:
        st.metric("⚡ 缓存率", stats["缓存命中率"])
    with col3:
        st.metric("🛡️ 拦截", stats["安全拦截数"])
    st.metric("📅 今日对话", stats["今日对话数"])

    st.divider()

    # --- 高频问题 ---
    st.subheader("🔥 高频问题 Top 5")
    top_questions = log.get_top_questions(5)
    if top_questions:
        df_data = []
        for i, (q, count) in enumerate(top_questions, 1):
            short_q = q[:30] + "..." if len(q) > 30 else q
            df_data.append({"排名": i, "问题": short_q, "次数": count})
        st.dataframe(pd.DataFrame(df_data), hide_index=True, use_container_width=True)
    else:
        st.caption("暂无数据")

    st.divider()

    # --- 用户反馈 ---
    st.subheader("💬 用户反馈")
    feedback_stats = log.get_feedback_stats()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("👍 好评", feedback_stats["好评"])
    with col2:
        st.metric("👎 差评", feedback_stats["差评"])
    st.metric("📈 好评率", feedback_stats["好评率"])

    # 🆕 ===== 每小时对话分布 =====
    st.subheader("🕐 今日对话分布")

    logger = st.session_state.logger
    hourly_data = logger.get_hourly_stats()
    if hourly_data:
        # 构建柱状图数据
        hours = [f"{h}时" for h, _ in hourly_data]
        counts = [c for _, c in hourly_data]

        chart_data = pd.DataFrame({"时段": hours, "对话数": counts})
        st.bar_chart(chart_data, x="时段", y="对话数", use_container_width=True)
    else:
        st.caption("今日暂无对话记录")

# ============================================================================
# 主聊天区域
# ============================================================================

# --- 显示历史消息 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 首次使用欢迎消息 ---
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown("""
        👋 您好！我是智能客服小智，可以帮您解决以下问题：

        - 📦 **查询订单**：提供订单号即可查询状态和物流
        - 🔄 **退货退款**：了解退货政策和流程
        - 📋 **政策咨询**：查询保修、物流等信息

        💡 **测试订单号**：12345、67890、11111

        请随时向我提问！
        """)

# --- 聊天输入框 ---
# st.chat_input 会在页面底部创建一个输入框
# 当用户输入文字并回车时，prompt 变量会接收到内容
# main.py 流式输出版本
# 在 main.py 中找到处理用户输入的部分，确保是这样的：

if prompt := st.chat_input("请输入您的问题..."):

    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 流式显示 AI 回复
    with st.chat_message("assistant"):
        try:
            response = st.write_stream(
                st.session_state.agent.chat_stream(prompt)
            )
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"回复生成失败: {e}")

# ============================================================================
# 页脚
# ============================================================================
st.divider()
st.caption(
    "极客科技智能客服系统 v1.0 | "
    "客服时间: 9:00-18:00 | "
    "紧急问题请拨打 📞 400-888-8888"
)