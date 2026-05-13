"""
tools.py - 工具集（数据库版本）
================================================================================
【升级内容】
从模拟字典 → SQLite 真实数据库
所有查询都走 SQL，和真实生产环境一致
================================================================================
"""

from datetime import datetime
from database import Database


class CustomerServiceTools:
    """客服工具集（数据库版本）"""

    def __init__(self):
        """初始化工具集 - 连接真实数据库"""
        self.db = Database()
        print("✅ 工具集初始化成功！（数据库版本）")

    def _get_order(self, order_id: str) -> dict:
        """
        从数据库查询订单

        私有方法，被其他工具方法调用
        """
        self.db.connect()
        cursor = self.db.conn.cursor()

        cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()

        self.db.close()

        if row:
            # 把数据库行转成字典
            return dict(row)
        return None

    def query_order(self, order_id: str) -> str:
        """查询订单状态"""
        order = self._get_order(order_id)

        if not order:
            return f"❌ 未找到订单 {order_id}，请核实订单号"

        result = f"""
📦 订单详情
━━━━━━━━━━━━━━━━━━
订单号：{order['order_id']}
商品：{order['product']}
下单时间：{order['order_date']}
订单状态：{order['status']}
物流单号：{order['logistics']}"""

        if order['status'] == '已发货':
            result += f"\n当前位置：{order['location']}"
            if order.get('estimated_delivery'):
                result += f"\n预计送达：{order['estimated_delivery']}"

        return result

    def check_return_eligibility(self, order_id: str) -> str:
        """检查退货资格"""
        order = self._get_order(order_id)

        if not order:
            return f"❌ 未找到订单 {order_id}"

        order_date = datetime.strptime(order['order_date'], "%Y-%m-%d")
        days_since_order = (datetime.now() - order_date).days

        if order['status'] == '已签收':
            if days_since_order <= 7:
                return f"✅ 订单 {order_id} 符合7天无理由退货条件"
            elif days_since_order <= 15:
                return f"⚠️ 订单 {order_id} 已超过7天，但如有质量问题可在15天内换货"
            else:
                return f"❌ 订单 {order_id} 已超过退货/换货期限"
        elif order['status'] == '待发货':
            return f"✅ 订单 {order_id} 尚未发货，可以直接取消"
        else:
            return f"ℹ️ 订单 {order_id} 状态为'{order['status']}'，建议收到货后再申请退货"

    def calculate_refund_amount(self, order_id: str) -> str:
        """计算退款金额"""
        order = self._get_order(order_id)

        if not order:
            return f"❌ 未找到订单 {order_id}"

        amount = order.get('price', 0)

        return f"""
💰 退款计算
━━━━━━━━━━━━━━━━━━
订单号：{order_id}
商品：{order['product']}
订单金额：¥{amount}
退款金额：¥{amount}
退款方式：原路返回
预计到账：3-5个工作日"""

    def get_order_count(self) -> int:
        """获取订单总数（用于统计）"""
        self.db.connect()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders")
        count = cursor.fetchone()[0]
        return count


# 工具描述不变
TOOL_DESCRIPTIONS = """
【可用工具列表】

1. query_order(order_id: str) 
   用途：查询订单状态和物流信息

2. check_return_eligibility(order_id: str)
   用途：检查订单是否满足退货/换货条件

3. calculate_refund_amount(order_id: str)
   用途：计算退款金额

【使用规则】
- 用户提到订单号，先使用 query_order 查询
- 涉及退货退款，先用 check_return_eligibility 检查资格
- 确认可退款后，再用 calculate_refund_amount 计算金额
"""

# ============================================================================
# 测试代码
# ============================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("🔧 工具功能测试（数据库版本）")
    print("=" * 50)

    tools = CustomerServiceTools()

    print(f"\n📊 数据库中有 {tools.get_order_count()} 条订单\n")

    print("1. 查询订单 12345:")
    print(tools.query_order("12345"))

    print("\n2. 检查退货资格:")
    print(tools.check_return_eligibility("12345"))

    print("\n3. 计算退款金额:")
    print(tools.calculate_refund_amount("12345"))