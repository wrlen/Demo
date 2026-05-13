"""
tools.py - 标准化工具定义（通义千问原生 Function Calling）
================================================================================
【核心改进】
从"让 LLM 返回 JSON 字符串" → "使用 API 原生 Function Calling"

原生 Function Calling 的好处：
1. API 保证返回格式正确（不会解析失败）
2. API 能识别"不需要工具"的情况
3. 支持并行调用多个工具
================================================================================
"""

from database import Database
from datetime import datetime


class CustomerServiceToolsV2:
    """客服工具集 V2 - 支持原生 Function Calling"""

    def __init__(self):
        self.db = Database()
        print("✅ 工具集 V2 初始化成功！")

    def _get_order(self, order_id: str) -> dict:
        """从数据库查询订单"""
        self.db.connect()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()
        self.db.close()
        return dict(row) if row else None

    def query_order(self, order_id: str) -> str:
        """查询订单状态"""
        order = self._get_order(order_id)
        if not order:
            return f"未找到订单 {order_id}"

        result = f"订单{order_id}：商品{order['product']}，状态{order['status']}"
        if order['status'] == '已发货':
            result += f"，位置{order['location']}，物流{order['logistics']}"
        return result

    def check_return_eligibility(self, order_id: str) -> str:
        """检查退货资格"""
        order = self._get_order(order_id)
        if not order:
            return f"未找到订单 {order_id}"

        order_date = datetime.strptime(order['order_date'], "%Y-%m-%d")
        days = (datetime.now() - order_date).days

        if order['status'] == '已签收':
            if days <= 7:
                return f"订单{order_id}符合7天无理由退货"
            elif days <= 15:
                return f"订单{order_id}超过7天，但15天内可换货"
            else:
                return f"订单{order_id}已超退货期限"
        elif order['status'] == '待发货':
            return f"订单{order_id}未发货，可直接取消"
        return f"订单{order_id}状态为{order['status']}，建议收货后申请"

    def calculate_refund(self, order_id: str) -> str:
        """计算退款金额"""
        order = self._get_order(order_id)
        if not order:
            return f"未找到订单 {order_id}"
        return f"订单{order_id}({order['product']})退款金额：¥{order['price']}"

    def get_order_count(self) -> int:
        """获取订单总数"""
        self.db.connect()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders")
        count = cursor.fetchone()[0]
        return count


# ============================================================================
# 🆕 工具 Schema 定义（给 API 看的"函数签名"）
# ============================================================================

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "query_order",
            "description": "查询订单状态和物流信息。当用户想了解订单状态、快递位置时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单号，如 12345"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_return_eligibility",
            "description": "检查订单是否满足退货/换货条件。当用户想退货、退款、换货时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单号，如 12345"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_refund",
            "description": "计算订单退款金额。确认可以退款后调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单号，如 12345"
                    }
                },
                "required": ["order_id"]
            }
        }
    }
]
CustomerServiceTools = CustomerServiceToolsV2
TOOL_DESCRIPTIONS = TOOL_SCHEMAS