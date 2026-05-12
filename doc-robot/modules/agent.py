import json
import re
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, DOCS_DIR
from modules.tools import read_doc, propose_pr, preview_changes


AGENT_SYSTEM_PROMPT = """你是文档更新助手，根据用户提供的 Changelog 自动更新技术文档并提 PR。

工作流程：
1. 仔细分析 Changelog，列出所有受影响的文档
2. 用 read_doc 逐个读取旧文档内容
3. 基于 Changelog 生成更新后的完整文档内容
4. 生成 commit message（格式：docs: 根据Changelog更新{章节名}）
5. 对于每个要更新的文档，展示变更预览并等待确认后才能提交

重要规则：
- 保持文档原有的结构和格式
- 基于 Changelog 精确修改，不要添加 Changelog 里没有的内容
- 删除的内容要在 Changelog 中明确标注
- commit message 使用中文，简洁描述变更内容
- 总共最多执行10个步骤"""


@tool
def read_doc_tool(file_path: str) -> str:
    """读取 data/docs/ 下指定文档的完整内容。file_path 是相对路径如 'api-guide.md'"""
    return read_doc(file_path)


def build_agent():
    """构建文档更新 Agent。"""
    llm = ChatOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        model=LLM_MODEL,
        temperature=0.3,
    )

    agent = create_agent(
        model=llm,
        tools=[read_doc_tool],
        system_prompt=AGENT_SYSTEM_PROMPT,
    )
    return agent


def run_agent(changelog: str) -> dict[str, Any]:
    """执行文档更新 Agent。"""
    agent = build_agent()

    prompt = f"""以下是需要处理的 Changelog：

{changelog}

请按步骤执行：
1. 分析 Changelog，确定需要更新哪些文档
2. 用 read_doc_tool 读取相关文档
3. 输出每个文档的更新内容（完整文档，不要省略）
4. 为每个变更生成 commit message

注意：输出更新后的文档内容时，用以下格式标记：
<<<FILE: 文件名>>>
更新后的完整文档内容...
<<<END>>>

commit message 用以下格式：
<<<COMMIT: 文件名>>>
docs: 变更描述
<<<END>>>"""

    config = {"configurable": {"max_iterations": 10}}

    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config=config,
        )

        # 提取 Agent 输出
        messages = result.get("messages", [])
        output_text = ""
        for msg in messages:
            if hasattr(msg, "content") and isinstance(msg.content, str):
                output_text += msg.content + "\n"

        # 解析文件更新
        updates = _parse_agent_output(output_text)

        if not updates:
            return {
                "status": "no_changes",
                "summary": "Agent 未识别到需要更新的文档",
                "pr_url": "",
                "details": output_text,
            }

        # 展示预览
        previews = []
        for upd in updates:
            prev = preview_changes(
                upd["file_path"], upd["new_content"], upd["commit_message"]
            )
            previews.append(prev)

        return {
            "status": "pending_confirm",
            "summary": f"准备更新 {len(updates)} 个文档",
            "updates": updates,
            "previews": previews,
            "pr_url": "",
            "details": output_text,
        }

    except Exception as e:
        return {
            "status": "error",
            "summary": f"Agent 执行失败: {e}",
            "pr_url": "",
            "details": str(e),
        }


def _parse_agent_output(text: str) -> list[dict]:
    """从 Agent 输出中解析文件更新。"""
    updates = []

    # 匹配 <<<FILE: ...>>> ... <<<END>>>
    file_pattern = re.compile(
        r"<<<FILE:\s*(.+?)>>>\s*(.*?)<<<END>>>", re.DOTALL
    )
    commit_pattern = re.compile(
        r"<<<COMMIT:\s*(.+?)>>>\s*(.*?)<<<END>>>", re.DOTALL
    )

    files = file_pattern.findall(text)
    commits = commit_pattern.findall(text)

    commit_map = {fn.strip(): msg.strip() for fn, msg in commits}

    for filename, content in files:
        filename = filename.strip()
        updates.append({
            "file_path": filename,
            "new_content": content.strip(),
            "commit_message": commit_map.get(filename, f"docs: 更新{filename}"),
        })

    return updates


def confirm_and_submit(
    updates: list[dict],
    confirmed_files: list[str],
    repo_path: str = ".",
) -> dict[str, Any]:
    """用户确认后提交变更。

    Args:
        updates: 要提的更新列表
        confirmed_files: 用户确认的文件名列表
        repo_path: 仓库路径
    """
    pr_urls = []
    for upd in updates:
        if upd["file_path"] in confirmed_files:
            pr_url = propose_pr(
                upd["file_path"],
                upd["new_content"],
                upd["commit_message"],
                repo_path,
            )
            pr_urls.append(pr_url)

    return {
        "status": "success",
        "summary": f"已提交 {len(pr_urls)} 个变更",
        "pr_url": pr_urls[0] if pr_urls else "",
        "pr_urls": pr_urls,
    }