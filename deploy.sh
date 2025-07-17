 #!/bin/bash

# 部署脚本
set -e

echo "开始部署人脸识别系统..."

# 1. 拉取最新代码
echo "拉取最新代码..."
git pull origin main

# 2. 构建 Docker 镜像
echo "构建 Docker 镜像..."
docker build -t face-recognition-system:latest .

# 3. 停止旧容器
echo "停止旧容器..."
docker-compose down || true

# 4. 启动新容器
echo "启动新容器..."
docker-compose up -d

# 5. 健康检查
echo "执行健康检查..."
sleep 10
curl -f http://localhost/api/health || {
    echo "健康检查失败！"
    exit 1
}

echo "部署完成！"