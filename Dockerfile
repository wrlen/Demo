# Dockerfile
# ====================================================================
# 每一行都是一层"缓存层"
# 把不常变的放上面（如依赖安装），常变的放下面（如代码复制）
# 这样重新构建时更快
# ====================================================================

# ① 基础镜像：自带 Python 3.11 的精简 Linux
FROM python:3.11-slim

# ② 设置工作目录
WORKDIR /app

# ③ 先复制依赖文件（不常变，放上面利用缓存）
COPY requirements.txt .

# ④ 安装依赖（这步很慢，但只有 requirements.txt 变了才重跑）
RUN pip install --no-cache-dir -r requirements.txt

# ⑤ 复制项目代码（常变，放下面）
COPY . .

# ⑥ 创建数据目录
RUN mkdir -p data chroma_db

# ⑦ 暴露端口
EXPOSE 8000

# ⑧ 启动命令
CMD ["python", "api.py"]