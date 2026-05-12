import os
import re
import glob
from datetime import datetime
from typing import Optional

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_core.documents import Document

from config import (
    DOCS_DIR,
    EMBEDDING_MODEL,
    EMBEDDING_DEVICE,
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION,
)


def split_markdown_by_headers(content: str, filename: str) -> list[Document]:
    """按 ## 和 ### 标题层级切分 Markdown，代码块不切断。"""
    lines = content.split("\n")
    documents: list[Document] = []

    in_code_block = False
    current_chunk_lines: list[str] = []
    current_h2: Optional[str] = None
    current_h3: Optional[str] = None

    def flush_chunk():
        nonlocal current_chunk_lines
        if not current_chunk_lines:
            return
        text = "\n".join(current_chunk_lines).strip()
        if not text:
            current_chunk_lines = []
            return

        # 拼接父标题作上下文前缀
        prefix_parts = [p for p in [current_h2, current_h3] if p]
        prefix = " > ".join(prefix_parts) if prefix_parts else ""
        full_text = f"[{prefix}]\n{text}" if prefix else text

        documents.append(Document(
            page_content=full_text,
            metadata={
                "filename": filename,
                "h2": current_h2 or "",
                "h3": current_h3 or "",
                "updated_at": datetime.now().isoformat(),
            }
        ))
        current_chunk_lines = []

    for line in lines:
        # 跟踪代码块状态
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            current_chunk_lines.append(line)
            continue

        if in_code_block:
            current_chunk_lines.append(line)
            continue

        # 检查标题
        h2_match = re.match(r"^##\s+(.+)", line)
        h3_match = re.match(r"^###\s+(.+)", line)
        h1_match = re.match(r"^#\s+(.+)", line)

        if h1_match:
            flush_chunk()
            current_h2 = h1_match.group(1).strip()
            current_h3 = None
            continue

        if h2_match:
            flush_chunk()
            current_h2 = h2_match.group(1).strip()
            current_h3 = None
            continue

        if h3_match:
            flush_chunk()
            current_h3 = h3_match.group(1).strip()
            continue

        current_chunk_lines.append(line)

    flush_chunk()
    return documents


class LocalEmbeddingFunction:
    """适配 ChromaDB 的本地 Embedding 函数。"""

    def __init__(self, model_name: str, device: str = "cpu"):
        self.model = SentenceTransformer(model_name, device=device)

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(
            input,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()


def run():
    """主流程：解析文档 → 切片 → 向量化 → 存入 ChromaDB。"""
    os.makedirs(DOCS_DIR, exist_ok=True)
    md_files = glob.glob(os.path.join(DOCS_DIR, "**", "*.md"), recursive=True)

    if not md_files:
        print(f"[loader] {DOCS_DIR} 下未找到 .md 文件，跳过入库")
        return

    all_docs: list[Document] = []
    for fp in md_files:
        with open(fp, encoding="utf-8") as f:
            content = f.read()
        filename = os.path.basename(fp)
        docs = split_markdown_by_headers(content, filename)
        all_docs.extend(docs)
        print(f"[loader] {filename}: {len(docs)} 个文本块")

    print(f"[loader] 总计 {len(all_docs)} 个文本块")

    # 初始化 Embedding 模型
    embedding_fn = LocalEmbeddingFunction(EMBEDDING_MODEL, EMBEDDING_DEVICE)

    # 初始化 ChromaDB
    client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=ChromaSettings(anonymized_telemetry=False),
    )

    # 删除旧集合（全量重建）
    try:
        client.delete_collection(CHROMA_COLLECTION)
    except Exception:
        pass

    collection = client.create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    # 批量写入
    batch_size = 50
    for i in range(0, len(all_docs), batch_size):
        batch = all_docs[i : i + batch_size]
        collection.add(
            ids=[f"chunk_{j}" for j in range(i, i + len(batch))],
            documents=[d.page_content for d in batch],
            metadatas=[d.metadata for d in batch],
        )

    print(f"[loader] 已写入 ChromaDB: {len(all_docs)} 条")


if __name__ == "__main__":
    run()