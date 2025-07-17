 #!/bin/bash

# Jenkins 设置脚本
echo "设置 Jenkins CI/CD 环境..."

# 1. 安装 Jenkins (Ubuntu/Debian)
echo "安装 Jenkins..."
wget -q -O - https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo apt-key add -
sudo sh -c 'echo deb https://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'
sudo apt-get update
sudo apt-get install -y jenkins

# 2. 安装 Docker
echo "安装 Docker..."
sudo apt-get install -y docker.io
sudo usermod -aG docker jenkins
sudo systemctl enable docker
sudo systemctl start docker

# 3. 安装 Docker Compose
echo "安装 Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. 配置 Jenkins
echo "配置 Jenkins..."
sudo systemctl start jenkins
sudo systemctl enable jenkins

# 5. 显示初始密码
echo "Jenkins 初始密码:"
sudo cat /var/lib/jenkins/secrets/initialAdminPassword

echo "Jenkins 设置完成！"
echo "访问: http://localhost:8080"