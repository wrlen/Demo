import os
import ssl
from pathlib import Path

# 设置环境变量 - 强制使用本地缓存
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(Path.home() / ".cache" / "huggingface" / "hub")
ssl._create_default_https_context = ssl._create_unverified_context

from sentence_transformers import SentenceTransformer, CrossEncoder
import chromadb
from chromadb.config import Settings as ChromaSettings
from rank_bm25 import BM25Okapi
import jieba

from modules import logger

from config import (
    EMBEDDING_MODEL,
    EMBEDDING_DEVICE,
    RERANKER_MODEL,
    RERANKER_DEVICE,
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION,
    RETRIEVAL_TOP_K,
    RERANK_TOP_K,
)


def _tokenize(text: str) -> list[str]:
    return list(jieba.cut(text))


class HybridRetriever:
    """混合检索器：BM25 关键词 + 语义向量 + 重排序。"""

    def __init__(self):
        # Embedding 模型 - 环境变量已配置为使用本地缓存
        self.embed_model = SentenceTransformer(EMBEDDING_MODEL, device=EMBEDDING_DEVICE)

        # ChromaDB
        self.client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_collection(CHROMA_COLLECTION)

        # 获取全量文档构建 BM25 索引
        all_data = self.collection.get(include=["documents", "metadatas"])
        self.all_docs = all_data["documents"] or []
        self.all_metas = all_data["metadatas"] or []
        if self.all_docs:
            tokenized = [_tokenize(d) for d in self.all_docs]
            self.bm25 = BM25Okapi(tokenized)

        # Reranker - 尝试加载，如果失败则跳过
        self.reranker = None
        try:
            self.reranker = CrossEncoder(RERANKER_MODEL, device=RERANKER_DEVICE)
        except Exception as e:
            logger.warning(f"Reranker 模型加载失败，将跳过重排序: {e}")

    def retrieve(self, query: str, top_k: int = None) -> list[dict]:
        """返回 Top-N 结果，每项含 content / filename / h2 / h3 / score。"""
        k = top_k or RERANK_TOP_K
        # 1. BM25 关键词检索
        bm25_results: list[tuple[int, float]] = []
        if self.all_docs:
            tokenized_query = _tokenize(query)
            bm25_scores = self.bm25.get_scores(tokenized_query)
            ranked = sorted(
                enumerate(bm25_scores), key=lambda x: x[1], reverse=True
            )[:RETRIEVAL_TOP_K]
            bm25_results = [(idx, score) for idx, score in ranked]

        # 2. 语义检索
        query_embedding = self.embed_model.encode(
            query, normalize_embeddings=True
        ).tolist()
        semantic_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=RETRIEVAL_TOP_K,
            include=["documents", "metadatas", "distances"],
        )

        # 3. 合并去重（用 idx 去重）
        seen_idx: set[int] = set()
        candidates: list[dict] = []

        # BM25 结果
        for idx, score in bm25_results:
            if idx not in seen_idx:
                seen_idx.add(idx)
                candidates.append({
                    "content": self.all_docs[idx],
                    "meta": self.all_metas[idx] or {},
                    "bm25_score": score,
                })

        # 语义结果
        for i, doc_id in enumerate(semantic_results["ids"][0]):
            idx = int(doc_id.replace("chunk_", ""))
            if idx not in seen_idx:
                seen_idx.add(idx)
                candidates.append({
                    "content": semantic_results["documents"][0][i],
                    "meta": semantic_results["metadatas"][0][i] or {},
                    "distance": semantic_results["distances"][0][i],
                })

        if not candidates:
            return []

        # 4. Reranker 重排序（如果可用）
        if self.reranker:
            pairs = [[query, c["content"]] for c in candidates]
            rerank_scores = self.reranker.predict(pairs)

            for c, score in zip(candidates, rerank_scores):
                c["score"] = float(score)

            candidates.sort(key=lambda x: x["score"], reverse=True)
            top5 = candidates[:k]
        else:
            # 如果没有reranker，直接取前K个作为结果
            # 优先使用BM25分数排序
            for c in candidates:
                c["score"] = c.get("bm25_score", 0) if "bm25_score" in c else (1.0 - c.get("distance", 1.0))
            candidates.sort(key=lambda x: x["score"], reverse=True)
            top5 = candidates[:k]

        return [
            {
                "content": c["content"],
                "filename": c["meta"].get("filename", ""),
                "h2": c["meta"].get("h2", ""),
                "h3": c["meta"].get("h3", ""),
                "score": c["score"],
            }
            for c in top5
        ]


# 全局单例
_retriever: HybridRetriever | None = None


def get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever