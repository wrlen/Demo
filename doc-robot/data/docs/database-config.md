# 数据库配置指南

## 连接配置

默认数据库连接参数：

```yaml
database:
  host: localhost
  port: 3306
  user: app_user
  charset: utf8mb4
  pool_size: 10
  timeout: 30
```

## 支持的数据类型

### 字符串类型
- VARCHAR: 变长字符串，最大 65535 字符
- TEXT: 长文本，最大 65535 字节
- LONGTEXT: 超长文本，最大 4GB

### 数字类型
- INT: 整数，范围 -2147483648 到 2147483647
- BIGINT: 大整数
- DECIMAL: 精确小数

## 索引优化

### 创建索引

```sql
CREATE INDEX idx_name ON users(name);
CREATE UNIQUE INDEX idx_email ON users(email);
```

### 索引使用规则

1. WHERE 子句中的列优先建索引
2. 联合索引遵循最左前缀原则
3. 避免在索引列上使用函数

## 备份策略

### 全量备份

每天凌晨 2 点自动执行全量备份：

```bash
mysqldump -u root -p database_name > backup.sql
```

### 增量备份

每小时执行一次 binlog 备份。