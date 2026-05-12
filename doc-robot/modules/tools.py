import os
import time
from pathlib import Path

from git import Repo, GitCommandError

from config import DOCS_DIR, GIT_BASE_BRANCH

# 路径白名单：仅允许 data/docs/ 下操作
DOCS_ROOT = Path(DOCS_DIR).resolve()


def _is_safe_path(file_path: str) -> bool:
    """检查路径是否在白名单内，防止路径穿越攻击。"""
    try:
        resolved = (DOCS_ROOT / file_path).resolve()
        return resolved.is_relative_to(DOCS_ROOT)
    except (ValueError, OSError):
        return False


def read_doc(file_path: str) -> str:
    """读取 data/docs/ 下指定文件的完整内容。

    Args:
        file_path: 相对于 data/docs/ 的文件路径，如 "api-guide.md"

    Returns:
        文件纯文本内容，或错误信息
    """
    if not _is_safe_path(file_path):
        return f"[错误] 不允许访问该路径: {file_path}"

    full_path = DOCS_ROOT / file_path
    if not full_path.exists():
        return f"[错误] 文件不存在: {file_path}"

    try:
        return full_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"[错误] 读取文件失败: {e}"


def propose_pr(
    file_path: str,
    new_content: str,
    commit_message: str,
    repo_path: str = ".",
) -> str:
    """将新内容写入文件，创建分支并生成 PR 链接。

    Args:
        file_path: 相对于 data/docs/ 的路径
        new_content: 更新后的完整文档内容
        commit_message: 提交信息
        repo_path: Git 仓库路径，默认当前目录

    Returns:
        PR 链接或错误信息
    """
    if not _is_safe_path(file_path):
        return f"[错误] 不允许访问该路径: {file_path}"

    full_path = DOCS_ROOT / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入新内容
    full_path.write_text(new_content, encoding="utf-8")

    # Git 操作
    try:
        repo = Repo(repo_path, search_parent_directories=True)

        # 检查工作区是否干净
        if repo.is_dirty(untracked_files=True):
            # 生成分支名
            filename = Path(file_path).stem
            timestamp = int(time.time())
            branch_name = f"doc-update/{filename}-{timestamp}"

            current_branch = repo.active_branch.name

            # 创建并切换到新分支
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()

            # 添加并提交
            relative_path = os.path.relpath(full_path, repo.working_dir)
            repo.index.add([relative_path])
            repo.index.commit(commit_message)

            # 生成 PR 链接（模拟）
            remote_url = _get_remote_url(repo)
            pr_url = f"{remote_url}/compare/{GIT_BASE_BRANCH}...{branch_name}?expand=1"

            # 切回原分支
            repo.heads[current_branch].checkout()

            return pr_url
        else:
            return "[错误] 没有检测到文件变更"

    except GitCommandError as e:
        return f"[错误] Git 操作失败: {e}"
    except Exception as e:
        return f"[错误] {e}"


def _get_remote_url(repo: Repo) -> str:
    """获取仓库的 Web URL。"""
    try:
        url = repo.remotes.origin.url
        if url.endswith(".git"):
            url = url[:-4]
        return url
    except Exception:
        return "https://github.com/unknown/repo"


def preview_changes(file_path: str, new_content: str, commit_message: str) -> str:
    """生成变更预览，供 Agent 确认用。"""
    old_content = read_doc(file_path)
    return (
        f"=== 变更预览 ===\n"
        f"文件: {file_path}\n"
        f"提交信息: {commit_message}\n\n"
        f"--- 旧内容 ---\n{old_content}\n"
        f"--- 新内容 ---\n{new_content}\n"
        f"================"
    )