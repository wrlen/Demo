import os
import ssl
from dotenv import load_dotenv

# 使用 HuggingFace 镜像源解决 SSL 证书问题
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 禁用 SSL 证书验证以解决证书问题
ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv()

# LLM
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qvq-max-2025-03-25")

# Embedding
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")

# Reranker
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
RERANKER_DEVICE = os.getenv("RERANKER_DEVICE", "cpu")

# ChromaDB
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "doc_robot")

# Retrieval
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "20"))
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "5"))

# Git
GIT_BASE_BRANCH = os.getenv("GIT_BASE_BRANCH", "main")
GIT_REMOTE = os.getenv("GIT_REMOTE", "origin")

# Service
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Docs
DOCS_DIR = os.getenv("DOCS_DIR", "./data/docs")