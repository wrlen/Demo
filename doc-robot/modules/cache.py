"""缓存模块 - 提供问答结果和检索结果的缓存功能"""
import time
from typing import Any, Dict, Optional
from functools import wraps


class SimpleCache:
    """简单的内存缓存实现"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        初始化缓存
        :param max_size: 最大缓存条目数
        :param ttl: 缓存有效期（秒），默认为1小时
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, dict] = {}
    
    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_parts = []
        for arg in args:
            key_parts.append(str(arg))
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        return "|".join(key_parts)
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if time.time() > entry["expire_at"]:
            del self._cache[key]
            return None
        
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值"""
        # 如果缓存已满，删除最早的条目
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["created_at"])
            del self._cache[oldest_key]
        
        expire_at = time.time() + (ttl or self.ttl)
        self._cache[key] = {
            "value": value,
            "created_at": time.time(),
            "expire_at": expire_at
        }
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
    
    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        now = time.time()
        valid_count = sum(1 for entry in self._cache.values() if entry["expire_at"] > now)
        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_count,
            "invalid_entries": len(self._cache) - valid_count
        }


# 全局缓存实例
_qa_cache = SimpleCache(max_size=500, ttl=3600)
_search_cache = SimpleCache(max_size=1000, ttl=1800)


def cache_qa(func):
    """问答结果缓存装饰器"""
    @wraps(func)
    def wrapper(question: str, session_id: str = "default", *args, **kwargs):
        key = f"qa|{session_id}|{question}"
        cached = _qa_cache.get(key)
        
        if cached is not None:
            return cached
        
        result = func(question, session_id, *args, **kwargs)
        
        # 缓存结果（排除对话历史相关的动态内容）
        cache_result = {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "intent": result.get("intent", "general"),
            "quality_score": result.get("quality_score", 100),
            "optimized": result.get("optimized", False)
        }
        _qa_cache.set(key, cache_result)
        
        return result
    
    return wrapper


def cache_search(func):
    """搜索结果缓存装饰器"""
    @wraps(func)
    def wrapper(query: str, *args, **kwargs):
        key = f"search|{query}"
        cached = _search_cache.get(key)
        
        if cached is not None:
            return cached
        
        result = func(query, *args, **kwargs)
        _search_cache.set(key, result)
        
        return result
    
    return wrapper


def get_cache_stats() -> dict:
    """获取缓存统计信息"""
    return {
        "qa_cache": _qa_cache.get_stats(),
        "search_cache": _search_cache.get_stats()
    }


def clear_all_cache():
    """清空所有缓存"""
    _qa_cache.clear()
    _search_cache.clear()