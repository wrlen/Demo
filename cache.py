"""
cache.py - 智能缓存模块
================================================================================
【为什么需要缓存？】

客服场景的特点：80%的问题都是高频重复问题
- "退货政策是什么？"
- "保修期多久？"
- "客服电话是多少？"

每次都用 LLM 回答这些"固定答案"的问题，浪费时间和金钱。

缓存策略：
1. 精确匹配缓存：问题完全一样 → 直接返回
2. 语义相似缓存（进阶）：问题意思相近 → 返回之前的答案
3. 工具结果缓存：相同的订单号查询结果 → 缓存一段时间
================================================================================
"""

import hashlib
import time
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta


class ResponseCache:
    """
    响应缓存 - 避免重复调用 LLM

    【设计思路】
    用一个字典存储：{问题 → (答案, 过期时间)}

    为什么不是永久缓存？
    - 政策可能变化
    - 库存、物流信息是动态的
    - 缓存过期保证信息新鲜
    """

    def __init__(self, ttl_seconds: int = 300):
        """
        初始化缓存

        参数:
            ttl_seconds: 缓存有效时间（秒）
            默认300秒 = 5分钟
            高频问题可以设更长，如3600秒 = 1小时
        """
        self.cache: Dict[str, Tuple[str, float]] = {}  # {key: (答案, 过期时间戳)}
        self.ttl = ttl_seconds  # TTL = Time To Live（存活时间）
        self.hits = 0  # 命中次数（统计用）
        self.misses = 0  # 未命中次数（统计用）

        print(f"✅ 缓存模块初始化成功！(TTL={ttl_seconds}秒)")

    def _make_key(self, text: str) -> str:
        """
        生成缓存键

        为什么用 MD5 而不是直接存原问题？
        1. 原问题可能很长，MD5固定32字符，省内存
        2. 统一格式，避免空格、标点导致"相同问题"匹配不上
        """
        # 先标准化：去空格、转小写
        normalized = text.strip().lower()
        # 生成 MD5 哈希
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    def get(self, query: str) -> Optional[str]:
        """
        从缓存中查找答案

        返回:
            有缓存且未过期 → 缓存的答案
            无缓存或已过期 → None
        """
        key = self._make_key(query)

        if key in self.cache:
            answer, expire_time = self.cache[key]

            # 检查是否过期
            if time.time() < expire_time:
                self.hits += 1
                print(f"⚡ [缓存命中] 问题: {query[:30]}...")
                return answer
            else:
                # 过期了，删除
                del self.cache[key]

        self.misses += 1
        print(f"🆕 [缓存未命中] 问题: {query[:30]}...")
        return None

    def set(self, query: str, answer: str):
        """将答案存入缓存"""
        key = self._make_key(query)
        expire_time = time.time() + self.ttl
        self.cache[key] = (answer, expire_time)
        print(f"💾 [已缓存] 问题: {query[:30]}... (过期时间: {self.ttl}秒后)")

    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "缓存命中": self.hits,
            "缓存未命中": self.misses,
            "命中率": f"{hit_rate:.1f}%",
            "缓存条目": len(self.cache),
            "TTL(秒)": self.ttl
        }


# ============================================================================
# 工具结果缓存（进阶）
# ============================================================================

class ToolResultCache:
    """
    工具结果缓存

    订单查询等操作的结果在短时间内不会变化，
    缓存工具结果避免重复查询数据库
    """

    def __init__(self, ttl_seconds: int = 60):
        """
        工具结果缓存时间比对话缓存短
        因为订单状态、物流信息变化更频繁
        """
        self.cache: Dict[str, Tuple[str, float]] = {}
        self.ttl = ttl_seconds
        print(f"✅ 工具结果缓存初始化成功！(TTL={ttl_seconds}秒)")

    def _make_key(self, tool_name: str, params: dict) -> str:
        """为工具调用生成缓存键"""
        raw = f"{tool_name}:{str(sorted(params.items()))}"
        return hashlib.md5(raw.encode('utf-8')).hexdigest()

    def get(self, tool_name: str, params: dict) -> Optional[str]:
        """从缓存获取工具结果"""
        key = self._make_key(tool_name, params)

        if key in self.cache:
            result, expire_time = self.cache[key]
            if time.time() < expire_time:
                print(f"⚡ [工具缓存命中] {tool_name}")
                return result
            else:
                del self.cache[key]

        print(f"🆕 [工具缓存未命中] {tool_name}")
        return None

    def set(self, tool_name: str, params: dict, result: str):
        """缓存工具结果"""
        key = self._make_key(tool_name, params)
        expire_time = time.time() + self.ttl
        self.cache[key] = (result, expire_time)


# ============================================================================
# 测试代码
# ============================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("⚡ 缓存模块测试")
    print("=" * 50)

    cache = ResponseCache(ttl_seconds=5)  # 5秒过期，方便测试

    # 第一次查询
    result = cache.get("退货政策是什么？")
    print(f"  结果: {result}\n")

    # 存入缓存
    cache.set("退货政策是什么？", "支持7天无理由退货，需保持商品完好")

    # 第二次查询（命中缓存）
    result = cache.get("退货政策是什么？")
    print(f"  结果: {result}\n")

    # 查看统计
    stats = cache.get_stats()
    print("📊 缓存统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")