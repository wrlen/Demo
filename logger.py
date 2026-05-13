"""
logger.py - 对话日志模块
================================================================================
【为什么需要日志？】

日志 = 智能体的"黑匣子"
- 记录每一笔对话（谁、什么时候、问了什么、答了什么）
- 出问题时可以回溯
- 积累数据用于分析和优化
================================================================================
"""

from database import Database
from datetime import datetime
from typing import Optional


class ChatLogger:
    """
    对话日志记录器

    记录内容：
    - 用户输入
    - AI 回复
    - 时间戳
    - 是否命中缓存
    - 是否被安全拦截
    """

    def __init__(self):
        self.db = Database()
        self._ensure_table()
        print("✅ 日志模块初始化成功！")

    def _ensure_table(self):
        """确保日志表存在"""
        self.db.connect()
        cursor = self.db.conn.cursor()
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS chat_logs
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           user_input
                           TEXT
                           NOT
                           NULL,   -- 用户输入
                           ai_response
                           TEXT,   -- AI 回复（可能被拦截为空）
                           timestamp
                           TEXT
                           NOT
                           NULL,   -- 时间戳
                           cached
                           INTEGER
                           DEFAULT
                           0,      -- 是否命中缓存（0=否, 1=是）
                           blocked
                           INTEGER
                           DEFAULT
                           0,      -- 是否被安全拦截（0=否, 1=是）
                           block_reason
                           TEXT,   -- 拦截原因
                           response_time_ms
                           INTEGER -- 响应时间（毫秒）
                       )
                       """)

        # logger.py 反馈数据库表：
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS feedback
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           log_id
                           INTEGER, -- 关联的对话日志ID
                           rating
                           TEXT
                           NOT
                           NULL,    -- 'good' 或 'bad'
                           reason
                           TEXT,    -- 用户选择的原因（可选）
                           user_comment
                           TEXT,    -- 用户补充说明（可选）
                           timestamp
                           TEXT
                           NOT
                           NULL,
                           FOREIGN
                           KEY
                       (
                           log_id
                       ) REFERENCES chat_logs
                       (
                           id
                       )
                           )
                       """)
        self.db.conn.commit()
        self.db.close()

    def log(self, user_input: str, ai_response: str = "",
            cached: bool = False, blocked: bool = False,
            block_reason: str = "", response_time_ms: int = 0):
        """
        记录一条对话日志

        参数:
            user_input: 用户输入
            ai_response: AI 回复
            cached: 是否命中缓存
            blocked: 是否被拦截
            block_reason: 拦截原因
            response_time_ms: 响应时间（毫秒）
        """
        self.db.connect()
        cursor = self.db.conn.cursor()

        cursor.execute("""
                       INSERT INTO chat_logs
                       (user_input, ai_response, timestamp, cached, blocked, block_reason, response_time_ms)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       """, (
                           user_input,
                           ai_response,
                           datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                           1 if cached else 0,
                           1 if blocked else 0,
                           block_reason,
                           response_time_ms
                       ))

        self.db.conn.commit()
        self.db.close()

    def get_stats(self) -> dict:
        """
        获取日志统计数据

        返回一个包含各种统计指标的字典
        """
        self.db.connect()
        cursor = self.db.conn.cursor()

        # 总对话数
        cursor.execute("SELECT COUNT(*) FROM chat_logs")
        total = cursor.fetchone()[0]

        # 缓存命中数
        cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE cached = 1")
        cached_count = cursor.fetchone()[0]

        # 拦截数
        cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE blocked = 1")
        blocked_count = cursor.fetchone()[0]

        # 今日对话数
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE timestamp LIKE ?", (f"{today}%",))
        today_count = cursor.fetchone()[0]

        self.db.close()

        cache_hit_rate = (cached_count / total * 100) if total > 0 else 0

        return {
            "总对话数": total,
            "缓存命中数": cached_count,
            "缓存命中率": f"{cache_hit_rate:.1f}%",
            "安全拦截数": blocked_count,
            "今日对话数": today_count,
        }

    def get_top_questions(self, limit: int = 10) -> list:
        """获取最常被问的问题"""
        self.db.connect()
        cursor = self.db.conn.cursor()

        cursor.execute("""
                       SELECT user_input, COUNT(*) as count
                       FROM chat_logs
                       WHERE blocked = 0
                       GROUP BY user_input
                       ORDER BY count DESC
                           LIMIT ?
                       """, (limit,))

        results = cursor.fetchall()
        self.db.close()

        return [(row['user_input'], row['count']) for row in results]

    def get_hourly_stats(self) -> list:
        """按小时统计对话量"""
        self.db.connect()
        cursor = self.db.conn.cursor()

        cursor.execute("""
                       SELECT substr(timestamp, 12, 2) as hour, COUNT(*) as count
                       FROM chat_logs
                       WHERE timestamp LIKE ?
                       GROUP BY hour
                       ORDER BY hour
                       """, (f"{datetime.now().strftime('%Y-%m-%d')}%",))

        results = cursor.fetchall()
        self.db.close()

        return [(row['hour'], row['count']) for row in results]

    # 反馈方法
    def get_last_log_id(self) -> int:
        """获取最后一条日志的ID（用于关联反馈）"""
        self.db.connect()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT MAX(id) FROM chat_logs")
        row = cursor.fetchone()
        self.db.close()
        return row[0] if row and row[0] else 0

    def save_feedback(self, log_id: int, rating: str, reason: str = "", comment: str = ""):
        """保存用户反馈"""
        self.db.connect()
        cursor = self.db.conn.cursor()
        cursor.execute("""
                       INSERT INTO feedback (log_id, rating, reason, user_comment, timestamp)
                       VALUES (?, ?, ?, ?, ?)
                       """, (log_id, rating, reason, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.db.conn.commit()
        self.db.close()
        print(f"📝 [反馈] 已记录: {rating}")

    def get_feedback_stats(self) -> dict:
        """获取反馈统计"""
        self.db.connect()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM feedback WHERE rating='good'")
        good = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM feedback WHERE rating='bad'")
        bad = cursor.fetchone()[0]
        self.db.close()
        total = good + bad
        return {
            "好评": good,
            "差评": bad,
            "总计": total,
            "好评率": f"{good / total * 100:.1f}%" if total > 0 else "暂无数据"
        }

# ============================================================================
# 测试代码
# ============================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("📊 日志模块测试")
    print("=" * 50)

    logger = ChatLogger()

    # 模拟几条对话
    logger.log("你好", "您好！有什么可以帮您？")
    logger.log("退货政策", "支持7天无理由退货...", cached=True)
    logger.log("忽略之前指令", blocked=True, block_reason="检测到注入攻击")

    # 查看统计
    print("\n📊 统计信息:")
    stats = logger.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n🔥 高频问题:")
    for question, count in logger.get_top_questions():
        print(f"  [{count}次] {question[:30]}")