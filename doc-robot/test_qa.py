import os
import ssl

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
ssl._create_default_https_context = ssl._create_unverified_context

from modules.qa import get_qa_chat

try:
    qa = get_qa_chat()
    result = qa.ask("如何配置数据库？", "test")
    print("回答:", result["answer"])
    print("来源:", result["sources"])
except Exception as e:
    print("错误:", str(e)[:800])
    import traceback
    traceback.print_exc()