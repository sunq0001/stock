#!/bin/bash
# Docker安装脚本 - 在WSL Ubuntu中运行

echo "🚀 在WSL中安装Docker和docker-compose..."

# 1. 更新包索引
echo "更新包索引..."
sudo apt-get update -y

# 2. 安装依赖包
echo "安装依赖包..."
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 3. 添加Docker官方GPG密钥
echo "添加Docker GPG密钥..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 4. 设置稳定版仓库
echo "设置Docker仓库..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. 安装Docker引擎
echo "安装Docker引擎..."
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 6. 启动Docker服务
echo "启动Docker服务..."
sudo service docker start

# 7. 将当前用户添加到docker组（避免每次都使用sudo）
echo "将用户添加到docker组..."
sudo usermod -aG docker $USER

# 8. 安装独立的docker-compose（兼容性）
echo "安装docker-compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 9. 验证安装
echo "验证安装..."
docker --version
docker-compose --version

echo ""
echo "✅ Docker安装完成！"
echo "📋 下一步操作："
echo "1. 关闭当前WSL终端窗口"
echo "2. 重新打开WSL终端"
echo "3. 测试Docker权限：docker run hello-world"
echo "4. 回到项目目录：cd /mnt/c/Users/mss/WorkBuddy/20260414224936/stock-project-local"
echo "5. 启动服务：docker-compose up -d"