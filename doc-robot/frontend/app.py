import streamlit as st
import requests
import json
import uuid
import os

API_BASE = "http://localhost:8001"

# 初始化会话状态
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_doc" not in st.session_state:
    st.session_state.current_doc = None
if "auto_submit" not in st.session_state:
    st.session_state.auto_submit = False
if "theme" not in st.session_state:
    st.session_state.theme = "light"

st.set_page_config(
    page_title="DOC-ROBOT",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 主题配置
THEMES = {
    "light": {
        "--bg-primary": "#ffffff",
        "--bg-secondary": "#f8fafc",
        "--bg-card": "#ffffff",
        "--bg-sidebar": "#f1f5f9",
        "--text-primary": "#1e293b",
        "--text-secondary": "#64748b",
        "--text-muted": "#94a3b8",
        "--border-color": "#e2e8f0",
        "--accent": "#3b82f6",
        "--accent-hover": "#2563eb",
        "--success": "#22c55e",
        "--warning": "#f59e0b",
        "--error": "#ef4444",
    },
    "dark": {
        "--bg-primary": "#0a0a0f",
        "--bg-secondary": "#111118",
        "--bg-card": "#15151f",
        "--bg-sidebar": "#0d0d12",
        "--text-primary": "#e2e8f0",
        "--text-secondary": "#94a3b8",
        "--text-muted": "#64748b",
        "--border-color": "#27272a",
        "--accent": "#4f9dff",
        "--accent-hover": "#3b82f6",
        "--success": "#22c55e",
        "--warning": "#f59e0b",
        "--error": "#ef4444",
    }
}

current_theme = THEMES[st.session_state.theme]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}}

:root {{
    --bg-primary: {current_theme['--bg-primary']};
    --bg-secondary: {current_theme['--bg-secondary']};
    --bg-card: {current_theme['--bg-card']};
    --bg-sidebar: {current_theme['--bg-sidebar']};
    --text-primary: {current_theme['--text-primary']};
    --text-secondary: {current_theme['--text-secondary']};
    --text-muted: {current_theme['--text-muted']};
    --border-color: {current_theme['--border-color']};
    --accent: {current_theme['--accent']};
    --accent-hover: {current_theme['--accent-hover']};
    --success: {current_theme['--success']};
    --warning: {current_theme['--warning']};
    --error: {current_theme['--error']};
}}

html, body, .stApp {{
    background: var(--bg-primary);
    color: var(--text-primary);
}}

.main-header {{
    padding: 1.5rem 2rem;
    border-bottom: 1px solid var(--border-color);
}}

.header-title {{
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
}}

.header-subtitle {{
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin-top: 0.25rem;
}}

.stSidebar {{
    background: var(--bg-sidebar) !important;
}}

.sidebar-section {{
    padding: 1rem;
    background: var(--bg-sidebar);
    border-bottom: 1px solid var(--border-color);
}}

.sidebar-title {{
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.75rem;
}}

.nav-item {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.625rem 0.75rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    color: var(--text-secondary);
    font-size: 0.9rem;
}}

.nav-item:hover {{
    background: var(--bg-secondary);
    color: var(--text-primary);
}}

.nav-item.active {{
    background: rgba(59, 130, 246, 0.1);
    color: var(--accent);
    font-weight: 500;
}}

.card {{
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}}

.card-header {{
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 1.25rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border-color);
}}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    color: var(--text-primary);
    font-size: 0.9rem;
    padding: 0.75rem;
}}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {{
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}}

.stButton > button {{
    background: var(--accent);
    border: none;
    color: white;
    font-weight: 500;
    font-size: 0.9rem;
    padding: 0.625rem 1.25rem;
    border-radius: 8px;
    transition: all 0.2s ease;
}}

.stButton > button:hover {{
    background: var(--accent-hover);
}}

.response-box {{
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 1rem;
    margin-top: 1rem;
}}

.response-content {{
    font-size: 0.9rem;
    line-height: 1.7;
    color: var(--text-primary);
}}

.sources-tag {{
    display: inline-block;
    background: rgba(59, 130, 246, 0.1);
    color: var(--accent);
    padding: 0.25rem 0.625rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
    margin-top: 0.75rem;
}}

.status-badge {{
    display: inline-block;
    padding: 0.25rem 0.625rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
    margin-top: 0.5rem;
}}

.status-badge.success {{
    background: rgba(34, 197, 94, 0.1);
    color: var(--success);
}}

.status-badge.error {{
    background: rgba(239, 68, 68, 0.1);
    color: var(--error);
}}

.status-badge.warning {{
    background: rgba(245, 158, 11, 0.1);
    color: var(--warning);
}}

.status-badge.info {{
    background: rgba(59, 130, 246, 0.1);
    color: var(--accent);
}}

.history-item {{
    background: var(--bg-secondary);
    border-radius: 6px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    cursor: pointer;
    transition: all 0.2s ease;
}}

.history-item:hover {{
    background: rgba(59, 130, 246, 0.08);
}}

.history-question {{
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
}}

.history-answer {{
    font-size: 0.8rem;
    color: var(--text-secondary);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}

.doc-list-item {{
    padding: 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
}}

.doc-list-item:hover {{
    background: var(--bg-secondary);
}}

.doc-name {{
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-primary);
}}

.doc-meta {{
    font-size: 0.75rem;
    color: var(--text-muted);
}}

.quick-action {{
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.85rem;
    color: var(--text-secondary);
}}

.quick-action:hover {{
    background: rgba(59, 130, 246, 0.08);
    border-color: var(--accent);
    color: var(--accent);
}}

.system-status {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
}}

.status-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
}}

.status-dot.online {{
    background: var(--success);
}}

.status-dot.offline {{
    background: var(--error);
}}

.doc-content {{
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 1.25rem;
    margin-top: 1rem;
    white-space: pre-wrap;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 0.85rem;
    line-height: 1.6;
}}

.skeleton-box {{
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 1rem;
    margin-top: 1rem;
}}

.skeleton-line {{
    height: 16px;
    background: linear-gradient(90deg, var(--border-color) 25%, var(--bg-card) 50%, var(--border-color) 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s infinite;
    border-radius: 4px;
    margin-bottom: 0.75rem;
}}

.skeleton-line:nth-child(2) {{
    width: 80%;
}}

.skeleton-line:nth-child(3) {{
    width: 60%;
    margin-bottom: 0;
}}

@keyframes skeleton-loading {{
    0% {{ background-position: 200% 0; }}
    100% {{ background-position: -200% 0; }}
}}

.error-box {{
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: 8px;
    padding: 1rem;
    margin-top: 1rem;
}}

.error-icon {{
    font-size: 1.5rem;
    flex-shrink: 0;
}}

.error-content {{
    flex: 1;
}}

.error-title {{
    font-weight: 600;
    color: var(--error);
    margin-bottom: 0.25rem;
}}

.error-message {{
    font-size: 0.85rem;
    color: var(--text-secondary);
}}

.quality-score {{
    display: inline-block;
    padding: 0.25rem 0.625rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
    margin-top: 0.75rem;
    background: rgba(34, 197, 94, 0.1);
}}

.search-result-item {{
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    border-left: 3px solid var(--accent);
}}

.search-result-title {{
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}}

.search-result-content {{
    font-size: 0.85rem;
    color: var(--text-secondary);
    line-height: 1.5;
    margin-bottom: 0.75rem;
}}



/* 微信风格聊天界面 */
.chat-container {{
    display: flex;
    flex-direction: column;
    height: calc(100vh - 200px);
    min-height: 500px;
    background: var(--bg-secondary);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}}

.chat-header {{
    padding: 1.25rem 1.5rem;
    background: var(--bg-card);
    border-bottom: 1px solid var(--border-color);
    text-align: center;
}}

.chat-title {{
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
}}

.chat-subtitle {{
    font-size: 0.8rem;
    color: var(--text-muted);
}}

.chat-messages {{
    flex: 1;
    overflow-y: auto;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
}}

.chat-messages::-webkit-scrollbar {{
    width: 6px;
}}

.chat-messages::-webkit-scrollbar-track {{
    background: transparent;
}}

.chat-messages::-webkit-scrollbar-thumb {{
    background: var(--border-color);
    border-radius: 3px;
}}

.message {{
    display: flex;
    flex-direction: column;
    max-width: 75%;
}}

.user-message {{
    align-self: flex-end;
    align-items: flex-end;
}}

.assistant-message {{
    align-self: flex-start;
    align-items: flex-start;
}}

.message-avatar {{
    font-size: 1.5rem;
    margin-bottom: 0.375rem;
}}

.message-bubble {{
    border-radius: 12px;
    padding: 0.75rem 1rem;
    line-height: 1.6;
}}

.user-bubble {{
    background: var(--accent);
    color: white;
    border-bottom-right-radius: 4px;
}}

.assistant-bubble {{
    background: var(--bg-card);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    border-bottom-left-radius: 4px;
}}

.message-text {{
    font-size: 0.9rem;
    white-space: pre-wrap;
    word-break: break-word;
}}

.message-sources {{
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px solid var(--border-color);
}}

.message-role {{
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-top: 0.375rem;
}}

.chat-empty {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
}}

.empty-icon {{
    font-size: 4rem;
    margin-bottom: 1rem;
}}

.empty-title {{
    font-size: 1.1rem;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
}}

.empty-desc {{
    font-size: 0.85rem;
    margin-bottom: 1.5rem;
}}

.empty-tags {{
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    justify-content: center;
}}

.empty-tags span {{
    padding: 0.375rem 0.875rem;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    font-size: 0.8rem;
    color: var(--text-secondary);
}}

.chat-input-area {{
    padding: 1rem 1.25rem;
    background: var(--bg-card);
    border-top: 1px solid var(--border-color);
}}

.input-wrapper {{
    display: flex;
    gap: 0.75rem;
    align-items: center;
}}

.input-wrapper input {{
    flex: 1;
    padding: 0.875rem 1rem;
    border: 1px solid var(--border-color);
    border-radius: 24px;
    font-size: 0.9rem;
    background: var(--bg-secondary);
    color: var(--text-primary);
    outline: none;
    transition: all 0.2s ease;
}}

.input-wrapper input:focus {{
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}}

.input-wrapper input::placeholder {{
    color: var(--text-muted);
}}

.input-wrapper button {{
    padding: 0.875rem 1.75rem;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 24px;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
}}

.input-wrapper button:hover {{
    background: var(--accent-hover);
}}

</style>
""", unsafe_allow_html=True)


def check_backend_status():
    """检查后端服务状态"""
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def load_doc_content(doc_name):
    """加载文档内容"""
    docs_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'docs')
    doc_path = os.path.join(docs_dir, doc_name)
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"文档 '{doc_name}' 不存在"
    except Exception as e:
        return f"读取文档失败: {str(e)}"


def get_doc_list():
    """获取文档列表"""
    docs_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'docs')
    docs = []
    if os.path.exists(docs_dir):
        for filename in sorted(os.listdir(docs_dir)):
            if filename.endswith('.md'):
                filepath = os.path.join(docs_dir, filename)
                filesize = os.path.getsize(filepath)
                filesize_str = f"{filesize / 1024:.1f} KB" if filesize > 1024 else f"{filesize} B"
                docs.append({
                    "name": filename,
                    "size": filesize_str,
                    "updated": "2024-01-15"
                })
    return docs


backend_online = check_backend_status()


# 侧边栏
with st.sidebar:
    st.markdown("""
    <div class="main-header">
        <h1 class="header-title">📋 DOC-ROBOT</h1>
        <p class="header-subtitle">技术文档智能助手</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="system-status">', unsafe_allow_html=True)
    status_text = "服务正常" if backend_online else "服务离线"
    status_class = "online" if backend_online else "offline"
    st.markdown(f'<span class="status-dot {status_class}"></span> {status_text}', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-section">
        <div class="sidebar-title">功能菜单</div>
    """, unsafe_allow_html=True)

    nav_items = [
        ("💬", "智能问答", "chat"),
        ("📁", "文档浏览", "docs"),
        ("🔄", "文档更新", "update"),
        ("📊", "用户反馈", "feedback"),
    ]

    selected_nav = st.session_state.get("selected_nav", "chat")

    for icon, label, key in nav_items:
        is_active = selected_nav == key
        active_class = "active" if is_active else ""
        st.markdown(
            f'<div class="nav-item {active_class}" onclick="window.location.hash=\'{key}\'">',
            unsafe_allow_html=True
        )
        if st.button(f"{icon} {label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.selected_nav = key
            st.session_state.current_doc = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-section">
        <div class="sidebar-title">快捷操作</div>
    """, unsafe_allow_html=True)

    quick_actions = [
        "如何配置数据库？",
        "API 接口说明",
        "部署指南",
        "常见问题",
    ]

    for action in quick_actions:
        if st.button(action, key=f"quick_{action}", use_container_width=True):
            st.session_state.quick_question = action
            st.session_state.selected_nav = "chat"
            st.session_state.auto_submit = True
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-section">
        <div class="sidebar-title">会话管理</div>
    """, unsafe_allow_html=True)

    if st.button("🔄 新建会话", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.rerun()

    st.markdown(f'<p style="font-size: 0.75rem; color: var(--text-muted);">会话 ID: {st.session_state.session_id[:8]}...</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size: 0.75rem; color: var(--text-muted);">历史记录: {len(st.session_state.chat_history)} 条</p>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 服务状态
    st.markdown("""
    <div class="sidebar-section">
        <div class="sidebar-title">服务状态</div>
    """, unsafe_allow_html=True)
    
    try:
        import requests
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        status = "online" if resp.status_code == 200 else "offline"
    except:
        status = "offline"
    
    status_color = "var(--success)" if status == "online" else "var(--error)"
    st.markdown(f'<div class="system-status"><div class="status-dot" style="background: {status_color};"></div><span style="font-size: 0.8rem;">后端服务: {status}</span></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # 使用提示
    st.markdown("""
    <div class="sidebar-section">
        <div class="sidebar-title">使用提示</div>
        <div style="font-size: 0.75rem; color: var(--text-secondary); line-height: 1.6; margin-top: 0.5rem;">
            <p>💡 提问时尽量具体，如"如何配置数据库连接？"</p>
            <p>📚 支持上传 Markdown 格式文档</p>
            <p>🔍 使用搜索功能快速定位内容</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


# 主内容区
selected_nav = st.session_state.get("selected_nav", "chat")


def upload_document(file):
    """上传文档到后端"""
    if file is not None:
        try:
            resp = requests.post(
                f"{API_BASE}/documents/upload",
                files={"file": (file.name, file, "text/markdown")},
                timeout=30
            )
            if resp.status_code == 200:
                st.markdown('<span class="status-badge success">上传成功</span>', unsafe_allow_html=True)
                st.rerun()
            else:
                error_data = resp.json() if resp.content else {}
                error_msg = error_data.get("detail", "上传失败")
                st.markdown(f'<span class="status-badge error">{error_msg}</span>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<span class="status-badge error">上传失败: {str(e)}</span>', unsafe_allow_html=True)


def delete_document(filename):
    """删除文档"""
    try:
        resp = requests.delete(f"{API_BASE}/documents/{filename}", timeout=30)
        if resp.status_code == 200:
            st.markdown('<span class="status-badge success">删除成功</span>', unsafe_allow_html=True)
            st.session_state.current_doc = None
            st.rerun()
        else:
            error_data = resp.json() if resp.content else {}
            error_msg = error_data.get("detail", "删除失败")
            st.markdown(f'<span class="status-badge error">{error_msg}</span>', unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f'<span class="status-badge error">删除失败: {str(e)}</span>', unsafe_allow_html=True)


def rebuild_index():
    """重建文档索引"""
    try:
        resp = requests.post(f"{API_BASE}/documents/rebuild", timeout=60)
        if resp.status_code == 200:
            st.markdown('<span class="status-badge success">索引重建完成</span>', unsafe_allow_html=True)
        else:
            error_data = resp.json() if resp.content else {}
            error_msg = error_data.get("detail", "索引重建失败")
            st.markdown(f'<span class="status-badge error">{error_msg}</span>', unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f'<span class="status-badge error">索引重建失败: {str(e)}</span>', unsafe_allow_html=True)


def search_documents(query):
    """搜索文档"""
    if not query:
        return []
    
    try:
        resp = requests.get(f"{API_BASE}/search", params={"query": query, "limit": 10}, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("results", [])
        else:
            return []
    except Exception as e:
        return []


def show_skeleton():
    """显示骨架屏加载状态"""
    st.markdown('<div class="skeleton-box">', unsafe_allow_html=True)
    for _ in range(3):
        st.markdown('<div class="skeleton-line"></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def submit_question(question):
    """提交问题并获取回答"""
    if not question:
        st.warning("请输入问题")
        return
    
    # 显示骨架屏
    skeleton_placeholder = st.empty()
    with skeleton_placeholder.container():
        show_skeleton()
    
    try:
        resp = requests.post(
            f"{API_BASE}/chat",
            json={"question": question, "session_id": st.session_state.session_id},
            timeout=60
        )
        
        # 清除骨架屏
        skeleton_placeholder.empty()
        
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.chat_history.append({
                "question": question,
                "answer": data["answer"],
                "sources": data["sources"],
                "intent": data.get("intent", "general"),
                "quality_score": data.get("quality_score", 100),
                "optimized": data.get("optimized", False)
            })
            
            st.markdown('<div class="response-box">', unsafe_allow_html=True)
            st.markdown('<div class="response-content">', unsafe_allow_html=True)
            st.write(data["answer"])
            st.markdown('</div>', unsafe_allow_html=True)
            
            if data["sources"]:
                st.markdown(f'<span class="sources-tag">参考文档：{", ".join(data["sources"])}</span>', unsafe_allow_html=True)
            
            # 显示质量评分
            if data.get("quality_score"):
                score = data["quality_score"]
                score_color = "#22c55e" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"
                st.markdown(f'<span class="quality-score" style="color: {score_color};">质量评分: {score}分</span>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        elif resp.status_code == 500:
            error_data = resp.json() if resp.content else {}
            error_msg = error_data.get("detail", "服务器内部错误")
            show_error("服务器错误", error_msg, show_retry=True)
        else:
            show_error("请求失败", f"HTTP状态码: {resp.status_code}", show_retry=True)
            
    except requests.ConnectionError:
        skeleton_placeholder.empty()
        show_error("连接失败", "无法连接到后端服务，请检查服务是否正常运行", show_retry=True)
    except requests.Timeout:
        skeleton_placeholder.empty()
        show_error("请求超时", "请求超时，请稍后重试", show_retry=True)
    except Exception as e:
        skeleton_placeholder.empty()
        show_error("未知错误", str(e), show_retry=True)


def show_error(title, message, show_retry=False):
    """显示错误信息"""
    error_html = f'''
    <div class="error-box">
        <div class="error-icon">❌</div>
        <div class="error-content">
            <div class="error-title">{title}</div>
            <div class="error-message">{message}</div>
        </div>
    </div>
    '''
    st.markdown(error_html, unsafe_allow_html=True)
    
    if show_retry:
        if st.button("🔄 重试", key="retry_btn"):
            # 重新提交最后一个问题
            if st.session_state.chat_history:
                last_question = st.session_state.chat_history[-1]["question"]
                submit_question(last_question)


if selected_nav == "chat":
    st.markdown("""
    <style>
    .message-bubble {
        padding: 0.75rem 1rem;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        max-width: 70%;
    }
    .user-bubble {
        background: var(--accent);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    .assistant-bubble {
        background: var(--bg-card);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-bottom-left-radius: 4px;
    }
    .msg-sources {
        font-size: 0.7rem;
        color: var(--text-muted);
        margin-top: 0.5rem;
        padding-top: 0.5rem;
        border-top: 1px solid var(--border-color);
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.subheader("🤖 智能问答")
    
    if st.session_state.chat_history:
        for item in st.session_state.chat_history:
            st.markdown(f'<div class="message-bubble user-bubble">{item["question"]}</div>', unsafe_allow_html=True)
            sources = f'<div class="msg-sources">来源: {", ".join(item.get("sources", []))}</div>' if item.get("sources") else ""
            st.markdown(f'<div class="message-bubble assistant-bubble">{item["answer"]}{sources}</div>', unsafe_allow_html=True)
    else:
        st.info("💬 开始对话吧！我可以帮助您查阅文档、解答技术问题。")
    
    default_question = st.session_state.get("quick_question", "")
    if "quick_question" in st.session_state:
        del st.session_state.quick_question
    
    col1, col2 = st.columns([5, 1])
    with col1:
        question = st.text_input("", key="chat_input", label_visibility="hidden", placeholder="输入问题...", value=default_question)
    with col2:
        send_btn = st.button("发送", key="chat_send_btn", type="primary", use_container_width=True)
    
    if send_btn or st.session_state.get("auto_submit", False):
        submit_question(question)
        st.session_state.auto_submit = False
        st.rerun()


elif selected_nav == "docs":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3 class="card-header">📁 文档浏览</h3>', unsafe_allow_html=True)
    
    # 搜索框
    search_query = st.text_input("全文搜索", placeholder="输入关键词搜索文档内容...", key="doc_search")
    
    # 文件上传区域
    st.markdown('<div style="margin-bottom: 1.5rem;">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("上传 Markdown 文档", type="md", key="doc_uploader")
    if uploaded_file:
        upload_document(uploaded_file)
    st.markdown('</div>', unsafe_allow_html=True)
    
    docs = get_doc_list()
    
    # 处理搜索
    search_results = []
    if search_query:
        search_results = search_documents(search_query)
    
    if search_results:
        st.markdown(f'<h4 style="font-size: 0.95rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.75rem;">🔍 搜索结果 ({len(search_results)})</h4>', unsafe_allow_html=True)
        
        for i, result in enumerate(search_results):
            st.markdown('<div class="search-result-item">', unsafe_allow_html=True)
            st.markdown(f'<div class="search-result-title">📄 {result["filename"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="search-result-content">{result["content"]}</div>', unsafe_allow_html=True)
            if st.button(f"查看全文", key=f"view_search_{i}", use_container_width=False):
                st.session_state.current_doc = result["filename"]
            st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        if search_query:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🔍</div>
                <p style="font-size: 0.9rem;">未找到匹配的文档</p>
                <p style="font-size: 0.8rem; margin-top: 0.25rem;">尝试使用其他关键词搜索</p>
            </div>
            """, unsafe_allow_html=True)
        elif not docs:
            st.markdown("""
            <div style="text-align: center; padding: 3rem 2rem; color: var(--text-muted);">
                <div style="font-size: 4rem; margin-bottom: 1rem;">📂</div>
                <h4 style="font-size: 1.1rem; font-weight: 500; color: var(--text-secondary); margin-bottom: 0.5rem;">暂无文档</h4>
                <p style="font-size: 0.85rem; line-height: 1.6;">
                    上传 Markdown 文档后，我可以帮您分析和检索文档内容。<br>
                    支持 .md 格式的文档文件。
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for doc in docs:
                st.markdown('<div class="doc-list-item">', unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1.5])
                with col1:
                    st.markdown(f'<span class="doc-name">{doc["name"]}</span>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<span class="doc-meta">{doc["size"]}</span>', unsafe_allow_html=True)
                with col3:
                    st.markdown(f'<span class="doc-meta">{doc["updated"]}</span>', unsafe_allow_html=True)
                with col4:
                    view_key = f"view_{doc['name']}"
                    delete_key = f"delete_{doc['name']}"
                    
                    col_view, col_delete = st.columns([1, 1])
                    with col_view:
                        if st.button("查看", key=view_key, use_container_width=True):
                            st.session_state.current_doc = doc["name"]
                    with col_delete:
                        if st.button("🗑️", key=delete_key, use_container_width=True):
                            delete_document(doc["name"])
            
                st.markdown('</div>', unsafe_allow_html=True)
    
    # 显示当前选中的文档内容
    if st.session_state.current_doc:
        doc_content = load_doc_content(st.session_state.current_doc)
        st.markdown(f'<h4 style="font-size: 0.9rem; font-weight: 600; margin-top: 1.5rem;">📄 {st.session_state.current_doc}</h4>', unsafe_allow_html=True)
        st.markdown(f'<div class="doc-content">{doc_content}</div>', unsafe_allow_html=True)
    
    # 重建索引按钮
    if docs and not search_query:
        st.markdown('<div style="margin-top: 1.5rem;">', unsafe_allow_html=True)
        if st.button("🔄 重建索引", use_container_width=True):
            rebuild_index()
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


elif selected_nav == "update":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3 class="card-header">🔄 文档更新</h3>', unsafe_allow_html=True)
    
    changelog = st.text_area(
        "输入变更说明",
        placeholder="例如：新增了用户认证 API 接口...",
        height=150,
        key="changelog_input"
    )
    
    if st.button("分析 Changelog", type="primary"):
        if changelog:
            with st.spinner("分析中..."):
                try:
                    resp = requests.post(
                        f"{API_BASE}/agent",
                        json={"changelog": changelog, "session_id": st.session_state.session_id},
                        timeout=120
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.markdown(f'<span class="status-badge info">分析完成</span>', unsafe_allow_html=True)
                        st.markdown(f'<div class="response-box"><div class="response-content">{data["summary"]}</div></div>', unsafe_allow_html=True)
                        
                        if data.get("updates"):
                            st.markdown('<h4 style="font-size: 0.9rem; font-weight: 600; margin-top: 1rem;">建议更新的文档：</h4>', unsafe_allow_html=True)
                            for i, update in enumerate(data["updates"]):
                                st.markdown(f'<div class="response-box"><strong>{update["file"]}</strong><br>{update["summary"]}</div>', unsafe_allow_html=True)
                                
                                if st.button("提交变更", type="primary"):
                                    confirm_resp = requests.post(
                                        f"{API_BASE}/agent/confirm",
                                        json={"confirmed_files": [update["file"]], "session_id": st.session_state.session_id},
                                        timeout=60
                                    )
                                    if confirm_resp.status_code == 200:
                                        confirm_data = confirm_resp.json()
                                        st.markdown(f'<span class="status-badge success">{confirm_data["summary"]}</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="status-badge error">分析失败</span>', unsafe_allow_html=True)
                except requests.ConnectionError:
                    st.markdown('<span class="status-badge error">无法连接后端服务</span>', unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<span class="status-badge error">错误：{e}</span>', unsafe_allow_html=True)
        else:
            st.warning("请输入变更说明")
    
    st.markdown('</div>', unsafe_allow_html=True)


elif selected_nav == "feedback":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3 class="card-header">📊 用户反馈</h3>', unsafe_allow_html=True)
    
    if st.session_state.chat_history:
        last_chat = st.session_state.chat_history[-1]
        st.markdown('<div class="response-box">', unsafe_allow_html=True)
        st.markdown(f'<strong>最近问题：</strong>{last_chat["question"]}', unsafe_allow_html=True)
        st.markdown(f'<strong>回答：</strong>{last_chat["answer"]}', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        feedback_rating = st.radio("反馈评分", ("👍 有用", "👎 无用"))
        
        feedback_reason = st.text_input("反馈原因（可选）")
        
        if st.button("提交反馈", type="primary"):
            rating = "up" if feedback_rating == "👍 有用" else "down"
            try:
                resp = requests.post(
                    f"{API_BASE}/feedback",
                    json={
                        "session_id": st.session_state.session_id,
                        "question": last_chat["question"],
                        "answer": last_chat["answer"],
                        "rating": rating,
                        "reason": feedback_reason
                    },
                    timeout=30
                )
                if resp.status_code == 200:
                    st.markdown('<span class="status-badge success">反馈已提交</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="status-badge error">提交失败</span>', unsafe_allow_html=True)
            except requests.ConnectionError:
                st.markdown('<span class="status-badge error">无法连接后端服务</span>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<span class="status-badge error">错误：{e}</span>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color: var(--text-muted);">暂无对话记录</p>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)