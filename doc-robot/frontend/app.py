import streamlit as st
import requests

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="文档机器人", page_icon="📚", layout="wide")
st.title("📚 技术文档智能问答与更新机器人")

# 侧边栏：模式选择
mode = st.sidebar.radio("选择模式", ["💬 智能问答", "🔄 文档更新", "📊 用户反馈"])

# 会话ID
if "session_id" not in st.session_state:
    st.session_state.session_id = "default"

# ====== 模式1：智能问答 ======

if mode == "💬 智能问答":
    st.header("智能问答")

    question = st.text_input("输入你的问题", placeholder="例如：如何配置数据库连接？")

    if st.button("提问") and question:
        with st.spinner("思考中..."):
            try:
                resp = requests.post(
                    f"{API_BASE}/chat",
                    json={
                        "question": question,
                        "session_id": st.session_state.session_id,
                    },
                    timeout=60,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.markdown("### 回答")
                    st.write(data["answer"])
                    if data["sources"]:
                        st.caption(f"参考文档：{', '.join(data['sources'])}")
                else:
                    st.error(resp.json().get("detail", "请求失败"))
            except requests.ConnectionError:
                st.error("无法连接到后端服务，请确认已启动 uvicorn main:app")
            except Exception as e:
                st.error(f"请求异常: {e}")

    # 对话历史
    with st.expander("对话记忆说明"):
        st.info(
            "系统会保留最近3轮完整对话，更早的对话将被压缩为摘要。\n"
            "刷新页面后对话记忆会清空。"
        )

# ====== 模式2：文档更新 ======

elif mode == "🔄 文档更新":
    st.header("文档更新 Agent")

    st.markdown("粘贴 Changelog，Agent 会自动分析 → 更新文档 → 提 PR")

    changelog = st.text_area(
        "Changelog",
        placeholder="## 2026-05-11\n- 新增：API 认证从 Token 改为 OAuth2\n- 修改：数据库端口从 3306 改为 3307\n- 删除：/v1/old-api 接口",
        height=200,
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 分析 Changelog", use_container_width=True):
            with st.spinner("Agent 分析中..."):
                try:
                    resp = requests.post(
                        f"{API_BASE}/agent",
                        json={"changelog": changelog},
                        timeout=120,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.agent_result = data

                        if data["status"] == "pending_confirm":
                            st.success(f"分析完成：{data['summary']}")
                            st.session_state.pending_updates = data.get("updates", [])
                        else:
                            st.info(data.get("summary", "无变更"))
                    else:
                        st.error(resp.json().get("detail", "请求失败"))
                except requests.ConnectionError:
                    st.error("无法连接到后端服务")
                except Exception as e:
                    st.error(f"异常: {e}")

    # 显示预览
    if "agent_result" in st.session_state and st.session_state.agent_result.get("previews"):
        st.markdown("---")
        st.subheader("变更预览")

        previews = st.session_state.agent_result["previews"]
        updates = st.session_state.get("pending_updates", [])

        confirmed_files = []
        for i, preview in enumerate(previews):
            with st.expander(f"变更 {i+1}: {updates[i]['file_path']}"):
                st.code(preview, language="diff")
                if st.checkbox("确认提交此变更", key=f"confirm_{i}"):
                    confirmed_files.append(updates[i]["file_path"])

        if confirmed_files:
            if st.button("✅ 提交已确认的变更", type="primary"):
                with st.spinner("提交中..."):
                    try:
                        resp = requests.post(
                            f"{API_BASE}/agent/confirm",
                            json={"confirmed_files": confirmed_files},
                            timeout=30,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.success(f"提交成功！\nPR: {data.get('pr_url', '')}")
                            st.balloons()
                        else:
                            st.error(resp.json().get("detail", "提交失败"))
                    except Exception as e:
                        st.error(f"异常: {e}")

# ====== 模式3：用户反馈 ======

elif mode == "📊 用户反馈":
    st.header("提交反馈")
    st.markdown("帮助改进回答质量，您的反馈会被记录到 feedback.jsonl")

    fb_session = st.text_input("会话 ID", value="default")
    fb_question = st.text_area("原始问题")
    fb_answer = st.text_area("系统回答")
    fb_rating = st.radio("评分", ["up", "down"], horizontal=True)
    fb_reason = st.text_area("反馈原因（可选）")

    if st.button("📤 提交反馈"):
        if not fb_question or not fb_answer:
            st.warning("请填写问题和回答")
        else:
            try:
                resp = requests.post(
                    f"{API_BASE}/feedback",
                    json={
                        "session_id": fb_session,
                        "question": fb_question,
                        "answer": fb_answer,
                        "rating": fb_rating,
                        "reason": fb_reason,
                    },
                    timeout=10,
                )
                if resp.status_code == 200:
                    st.success("反馈已记录！")
                else:
                    st.error("提交失败")
            except requests.ConnectionError:
                st.error("无法连接到后端服务")