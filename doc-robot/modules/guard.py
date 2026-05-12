import re
import json
import time
from pathlib import Path

FEEDBACK_FILE = Path("feedback.jsonl")

# 输入护栏配置
MAX_QUERY_LENGTH = 2000

# 匹配代码注入模式
INJECTION_PATTERNS = re.compile(
    r"(\bimport\s+os\b|\b__import__\b|\beval\s*\(|\bexec\s*\(|"
    r"\bsubprocess\b|`[^`]*`|\$\(|&&|\|\|)",
    re.IGNORECASE,
)

# 输出护栏：疑似编造/幻觉的关键词
HALLUCINATION_KEYWORDS = re.compile(
    r"(编造|不确定|可能|大概|也许|猜测|我猜|或许)",
)

SAFE_REPLY = ("抱歉，我无法基于当前参考资料回答这个问题。请查阅官方文档或联系技术支持。")


def check_input(query: str) -> tuple[bool, str]:
    """输入护栏：检查查询是否安全。

    Returns:
        (is_safe, error_message)
    """
    if len(query) > MAX_QUERY_LENGTH:
        return False, f"查询长度超过限制（{MAX_QUERY_LENGTH}字符）"

    if INJECTION_PATTERNS.search(query):
        return False, "查询包含不安全的代码模式，已被拒绝"

    return True, ""


def check_output(answer: str) -> tuple[bool, str]:
    """输出护栏：检查回答是否包含疑似幻觉标记。

    Returns:
        (is_safe, safe_answer)
    """
    if HALLUCINATION_KEYWORDS.search(answer):
        return False, SAFE_REPLY
    return True, answer


def record_feedback(
    session_id: str,
    question: str,
    answer: str,
    rating: str,
    reason: str = "",
) -> None:
    """记录用户反馈到 feedback.jsonl。"""
    entry = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "session_id": session_id,
        "question": question,
        "answer": answer,
        "rating": rating,
        "reason": reason,
    }
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")