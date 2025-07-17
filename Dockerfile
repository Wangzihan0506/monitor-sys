# 多阶段构建 - 前端
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY front-vue3/package*.json ./
RUN npm ci --only=production
COPY front-vue3/ .
RUN npm run build

# 多阶段构建 - 后端
FROM python:3.9-slim AS backend-builder
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

# 生产环境镜像
FROM python:3.9-slim
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 复制后端代码和依赖
COPY --from=backend-builder /app /app/backend
COPY --from=backend-builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app/backend

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "/app/backend/app.py"]