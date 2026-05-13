"""
knowledge_base.py - RAG 知识库（多格式支持）
================================================================================
支持 TXT、MD 文件，不需要额外安装包
================================================================================
"""

import os
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from config import Config


class KnowledgeBase:
    """知识库 V2 - 多格式支持"""

    def __init__(self):
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=Config.DASHSCOPE_API_KEY
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
        )

        self.vector_store = None
        print("✅ 知识库 V2 初始化成功！")

    def _load_single_file(self, file_path: str) -> list:
        """
        加载单个文件
        根据后缀选择加载方式：
        .txt → TextLoader
        .md  → 手动读取（不依赖第三方包）
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.txt':
            loader = TextLoader(file_path, encoding='utf-8')
            return loader.load()

        elif ext == '.md':
            # 手动读取 MD 文件，不需要安装 markdown 包
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # 包装成 Document 对象
            return [Document(page_content=content, metadata={"source": file_path})]

        return []

    def load_documents(self, directory: str = "data"):
        """加载目录下所有文档"""
        print(f"📂 正在扫描目录: {directory}")

        all_chunks = []
        total_files = 0

        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()

                if ext not in ['.txt', '.md']:
                    continue

                try:
                    documents = self._load_single_file(file_path)
                    chunks = self.text_splitter.split_documents(documents)
                    all_chunks.extend(chunks)
                    total_files += 1
                    print(f"  ✅ {file}: {len(chunks)} 个片段")
                except Exception as e:
                    print(f"  ⚠️  {file}: 加载失败 - {e}")

        if not all_chunks:
            print("❌ 未找到任何文档")
            return 0

        print(f"📊 共加载 {total_files} 个文件，{len(all_chunks)} 个片段")

        self.vector_store = Chroma.from_documents(
            documents=all_chunks,
            embedding=self.embeddings,
            persist_directory="./chroma_db"
        )
        print("✅ 知识库构建完成！")
        return len(all_chunks)

    def search(self, query: str, k: int = 3) -> str:
        if not self.vector_store:
            return ""
        docs = self.vector_store.similarity_search(query, k=k)
        return "\n\n".join([doc.page_content for doc in docs])

    def load_existing(self):
        if os.path.exists("./chroma_db"):
            try:
                self.vector_store = Chroma(
                    persist_directory="./chroma_db",
                    embedding_function=self.embeddings
                )
                print("✅ 已加载现有知识库")
                return True
            except:
                pass
        print("⚠️  未找到知识库，请先构建")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("📚 知识库 V2")
    print("=" * 50)

    kb = KnowledgeBase()
    kb.load_documents("data")

    while True:
        try:
            q = input("\n🔍 搜索: ").strip()
            if q == 'quit':
                break
            if not q:
                continue
            result = kb.search(q)
            print(f"\n📚 结果:\n{result[:300]}")
        except KeyboardInterrupt:
            break