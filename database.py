"""
database.py - 数据库初始化与管理
================================================================================
【为什么要从字典换成数据库？】

字典（模拟）的问题：
- 重启程序数据就没了
- 不支持复杂查询（"查询所有已发货超过3天的订单"）
- 多个人同时访问会出问题
- 不符合实际生产环境

SQLite 的优势：
- 数据持久化（重启还在）
- 支持 SQL 查询
- 一个文件，零配置
- 和 MySQL 语法兼容，后续无缝迁移
================================================================================
"""

import sqlite3
import os
from datetime import datetime


class Database:
    """
    数据库管理类

    【SQLite 基础概念】
    - 数据库 = 一个 .db 文件
    - 表 = Excel 表格
    - 行 = 一条记录
    - 列 = 一个字段
    """

    def __init__(self, db_path: str = "customer_service.db"):
        """
        初始化数据库连接

        参数:
            db_path: 数据库文件路径
            如果文件不存在，SQLite 会自动创建
        """
        self.db_path = db_path
        self.conn = None
        print(f"✅ 数据库模块初始化成功！(文件: {db_path})")

    def connect(self):
        """建立数据库连接"""
        self.conn = sqlite3.connect(self.db_path)
        # 让查询结果可以用列名访问（像字典一样）
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def init_tables(self):
        """
        创建数据库表

        相当于创建"Excel 表格"的空白模板
        """
        self.connect()
        cursor = self.conn.cursor()

        # ===== 订单表 =====
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS orders
                       (
                           order_id
                           TEXT
                           PRIMARY
                           KEY,  -- 订单号（主键，唯一）
                           product
                           TEXT
                           NOT
                           NULL, -- 商品名称
                           price
                           REAL
                           NOT
                           NULL, -- 价格
                           status
                           TEXT
                           NOT
                           NULL, -- 状态：待发货/已发货/已签收
                           order_date
                           TEXT
                           NOT
                           NULL, -- 下单日期
                           logistics
                           TEXT, -- 物流单号
                           location
                           TEXT, -- 当前位置
                           estimated_delivery
                           TEXT  -- 预计送达日期
                       )
                       """)

        # ===== 对话日志表（用于分析） =====
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
                           NULL,
                           ai_response
                           TEXT
                           NOT
                           NULL,
                           timestamp
                           TEXT
                           NOT
                           NULL,
                           cached
                           INTEGER
                           DEFAULT
                           0 -- 是否命中缓存
                       )
                       """)

        self.conn.commit()
        self.close()
        print("✅ 数据库表创建成功！")

    def insert_sample_data(self):
        """
        插入示例数据
        替换之前的模拟字典
        """
        self.connect()
        cursor = self.conn.cursor()

        # 先清空旧数据
        cursor.execute("DELETE FROM orders")

        # 插入3条示例订单
        sample_orders = [
            ("12345", "智能手表 Pro", 1299, "已发货", "2024-12-20",
             "顺丰快递 SF1234567890", "郑州市中转站", "2024-12-25"),
            ("67890", "蓝牙耳机", 299, "待发货", "2024-12-23",
             "待分配", "仓库处理中", None),
            ("11111", "智能音箱", 599, "已签收", "2024-12-01",
             "已签收", "已送达", None),
        ]

        cursor.executemany("""
                           INSERT INTO orders
                           (order_id, product, price, status, order_date, logistics, location, estimated_delivery)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                           """, sample_orders)

        self.conn.commit()
        self.close()
        print("✅ 示例数据插入成功！(3条订单)")


# ============================================================================
# 测试代码
# ============================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("🗄️  数据库初始化")
    print("=" * 50)

    db = Database()

    # 初始化表结构
    db.init_tables()

    # 插入示例数据
    db.insert_sample_data()

    # 验证数据
    db.connect()
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM orders")
    rows = cursor.fetchall()

    print(f"\n📊 订单数据验证（共 {len(rows)} 条）:")
    for row in rows:
        print(f"  📦 {row['order_id']} | {row['product']} | ¥{row['price']} | {row['status']}")

    db.close()
    print("\n✅ 数据库初始化完成！")