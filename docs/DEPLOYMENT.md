# 漫剧自动化工作台 - 部署指南

## 目录

1. [部署方式概览](#1-部署方式概览)
2. [Docker部署（推荐）](#2-docker部署推荐)
3. [云服务器部署](#3-云服务器部署)
4. [GitHub Actions自动化部署](#4-github-actions自动化部署)
5. [故障排查](#5-故障排查)

---

## 1. 部署方式概览

本项目支持多种部署方式，根据你的需求选择：

| 部署方式 | 适用场景 | 难度 | 推荐度 |
|---------|---------|------|--------|
| **Docker Compose** | 本地开发、小型部署 | ⭐ | ⭐⭐⭐⭐⭐ |
| **云服务器** | 生产环境、自定义配置 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **GitHub Actions** | CI/CD自动化部署 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Vercel** | 仅前端快速部署 | ⭐ | ⭐⭐⭐ |

---

## 2. Docker部署（推荐）

### 2.1 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 可用内存
- 至少 10GB 可用磁盘空间

### 2.2 快速开始

#### 步骤1：克隆项目

```bash
git clone https://github.com/your-username/trae-demo.git
cd trae-demo
```

#### 步骤2：配置环境变量

```bash
# 复制环境变量模板
cp backend/.env.example backend/.env

# 编辑 .env 文件，填入你的配置
# 必填项：
# - API_KEY: 阿里云DashScope API密钥
```

**backend/.env 示例：**

```env
API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
API_KEY=sk-your-api-key-here
REDIS_URL=redis://redis:6379/0
DATABASE_URL=sqlite:///./demo.db
PORT=8000
```

#### 步骤3：启动所有服务

```bash
# 构建并启动所有容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f celery
docker-compose logs -f frontend
```

#### 步骤4：验证部署

```bash
# 检查容器状态
docker-compose ps

# 应该看到以下服务都在运行：
# - trae-redis
# - trae-backend
# - trae-celery
# - trae-frontend
# - trae-nginx
```

访问：
- **应用首页**：http://localhost
- **后端API**：http://localhost/api
- **API文档**：http://localhost/api/docs

### 2.3 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 停止并删除所有数据（包括数据库）
docker-compose down -v

# 重启特定服务
docker-compose restart backend

# 查看服务日志
docker-compose logs -f [service-name]

# 进入容器
docker-compose exec backend bash
docker-compose exec redis redis-cli

# 更新镜像并重新构建
docker-compose pull
docker-compose up -d --build

# 清理未使用的资源
docker system prune -a
```

### 2.4 数据持久化

Docker Compose配置已包含数据卷：

```yaml
volumes:
  redis_data:      # Redis数据
  backend_static:  # 静态文件（图片、音频、视频）
```

数据存储在Docker卷中，即使容器重启也不会丢失。

### 2.5 性能优化

#### 2.5.1 调整Celery Worker数量

编辑 `docker-compose.yml`：

```yaml
celery:
  deploy:
    replicas: 2  # 增加worker数量
```

#### 2.5.2 调整Redis内存限制

编辑 `docker-compose.yml`：

```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

---

## 3. 云服务器部署

### 3.1 服务器要求

| 配置 | 最低 | 推荐 |
|------|------|------|
| CPU | 2核 | 4核 |
| 内存 | 4GB | 8GB |
| 磁盘 | 20GB | 50GB SSD |
| 操作系统 | Ubuntu 20.04+ | Ubuntu 22.04 LTS |

### 3.2 部署步骤

#### 步骤1：连接服务器

```bash
ssh user@your-server-ip
```

#### 步骤2：安装Docker

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

#### 步骤3：克隆项目

```bash
git clone https://github.com/your-username/trae-demo.git
cd trae-demo
```

#### 步骤4：配置环境变量

```bash
cp backend/.env.example backend/.env
nano backend/.env  # 编辑配置文件
```

#### 步骤5：启动服务

```bash
docker-compose up -d
```

#### 步骤6：配置防火墙

```bash
# Ubuntu UFW
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 或使用iptables
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

#### 步骤7：配置域名（可选）

如果你有域名，配置DNS指向服务器IP，然后修改Nginx配置：

```nginx
server_name your-domain.com;
```

### 3.3 SSL证书配置（HTTPS）

#### 使用Let's Encrypt免费证书

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

#### 修改Nginx配置

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # ... 其他配置
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 3.4 监控和日志

#### 查看日志

```bash
# 实时日志
docker-compose logs -f

# 查看最近100行
docker-compose logs --tail=100

# 导出日志
docker-compose logs > app.log
```

#### 监控容器资源

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
docker system df
```

### 3.5 备份策略

#### 数据库备份

```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d_%H%M%S)
docker cp trae-backend:/app/demo.db $BACKUP_DIR/demo_$DATE.db
find $BACKUP_DIR -name "demo_*.db" -mtime +7 -delete
EOF

chmod +x backup.sh

# 添加到crontab（每天凌晨2点备份）
crontab -e
0 2 * * * /path/to/backup.sh
```

#### 静态文件备份

```bash
# 备份静态文件
docker run --rm -v trae-demo_backend_static:/data -v $(pwd)/backup:/backup alpine tar czf /backup/static_$(date +%Y%m%d).tar.gz /data
```

---

## 4. GitHub Actions自动化部署

### 4.1 创建GitHub Actions工作流

创建 `.github/workflows/deploy.yml`：

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Deploy to server
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.SERVER_HOST }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /path/to/trae-demo
          git pull origin main
          docker-compose pull
          docker-compose up -d --build
          docker system prune -f
```

### 4.2 配置GitHub Secrets

在GitHub仓库设置中添加以下Secrets：

| Secret名称 | 说明 |
|-----------|------|
| `SERVER_HOST` | 服务器IP地址 |
| `SERVER_USER` | SSH用户名 |
| `SSH_PRIVATE_KEY` | SSH私钥内容 |

### 4.3 手动触发部署

1. 访问GitHub仓库的Actions页面
2. 选择"Deploy to Production"工作流
3. 点击"Run workflow"按钮

---

## 5. 故障排查

### 5.1 常见问题

#### 问题1：容器启动失败

```bash
# 查看容器日志
docker-compose logs [service-name]

# 检查容器状态
docker-compose ps

# 重新构建容器
docker-compose up -d --build
```

#### 问题2：数据库连接失败

```bash
# 检查数据库文件权限
docker-compose exec backend ls -la demo.db

# 重启后端服务
docker-compose restart backend
```

#### 问题3：Celery任务不执行

```bash
# 检查Celery日志
docker-compose logs celery

# 检查Redis连接
docker-compose exec redis redis-cli ping

# 重启Celery
docker-compose restart celery
```

#### 问题4：内存不足

```bash
# 查看内存使用
docker stats

# 清理未使用的资源
docker system prune -a

# 限制容器内存（编辑docker-compose.yml）
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
```

#### 问题5：端口冲突

```bash
# 检查端口占用
netstat -tulpn | grep :80

# 修改docker-compose.yml中的端口映射
ports:
  - "8080:80"  # 使用8080端口
```

### 5.2 日志分析

#### 后端日志

```bash
# 查看后端错误日志
docker-compose logs backend | grep ERROR

# 查看API请求日志
docker-compose logs backend | grep "GET\|POST"
```

#### Celery日志

```bash
# 查看任务执行情况
docker-compose logs celery | grep "Task.*succeeded\|Task.*failed"

# 查看任务队列
docker-compose exec redis redis-cli
> LLEN celery
```

### 5.3 性能调优

#### 数据库优化

```bash
# 使用PostgreSQL替代SQLite（生产环境推荐）
# 修改 backend/.env:
DATABASE_URL=postgresql://user:password@postgres:5432/trae_db
```

#### 缓存优化

```bash
# 启用Redis缓存
# 在 backend/main.py 中添加：
from redis import Redis
redis_client = Redis.from_url(settings.REDIS_URL)
```

#### CDN加速

```bash
# 使用CDN加速静态文件
# 修改 nginx.conf：
location /static/ {
    proxy_pass https://your-cdn-domain.com/static/;
}
```

---

## 6. 安全建议

### 6.1 基本安全措施

1. **不要提交敏感信息**
   - 确保 `.env` 文件在 `.gitignore` 中
   - 使用环境变量或密钥管理服务

2. **定期更新依赖**
   ```bash
   cd backend && pip install --upgrade -r requirements.txt
   cd frontend && npm update
   ```

3. **限制API访问**
   - 使用API网关
   - 实现速率限制
   - 添加认证机制

4. **启用HTTPS**
   - 使用Let's Encrypt免费证书
   - 强制HTTPS重定向

### 6.2 监控和告警

```bash
# 安装监控工具
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v /path/to/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# 安装Grafana
docker run -d \
  --name grafana \
  -p 3001:3000 \
  grafana/grafana
```

---

## 7. 扩展部署

### 7.1 Kubernetes部署

创建 `k8s/deployment.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trae-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: trae-backend
  template:
    metadata:
      labels:
        app: trae-backend
    spec:
      containers:
      - name: backend
        image: trae-demo/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: trae-secrets
              key: api-key
```

### 7.2 负载均衡

使用Nginx负载均衡多个后端实例：

```nginx
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

---

**文档版本**: v1.0
**创建日期**: 2026-05-12
**维护者**: 项目团队
