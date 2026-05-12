# 部署运维手册

## 部署方式

### Docker 部署（推荐）

```bash
docker compose up --build
```

首次启动后执行数据入库：

```bash
docker compose exec app python -c "from modules.loader import run; run()"
```

### 本地部署

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## 环境要求

- Python 3.12+
- 内存 8GB+（Embedding 模型需要）
- 磁盘 20GB+（模型文件约 2GB）

## 常见错误

### 错误码 500

内部服务器错误，检查：
1. LLM API 密钥是否配置
2. 网络是否能连通阿里云百炼
3. ChromaDB 数据是否已入库

### 错误码 503

服务暂不可用，可能原因：
- Embedding 模型正在加载中（首次启动需 30-60 秒）
- ChromaDB 数据库文件损坏，需重新入库

## 监控

### 健康检查

```bash
curl http://localhost:8000/health
```

返回 `{"status": "ok"}` 即服务正常。

### 日志

应用日志输出到 stdout，Docker 部署时通过 `docker compose logs` 查看。