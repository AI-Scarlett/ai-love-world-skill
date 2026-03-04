#!/bin/bash
# 远程部署脚本 - 从本地执行，远程部署到服务器
# 使用方法：./remote_deploy.sh

set -e

echo "========================================"
echo "🚀 远程部署到服务器"
echo "========================================"
echo ""

# 服务器配置
SERVER_IP="8.148.230.65"
SERVER_USER="root"
PROJECT_DIR="/var/www/ailoveworld"

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo_step() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. 测试 SSH 连接
echo "测试 SSH 连接..."
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} "echo '连接成功'" > /dev/null 2>&1; then
    echo_step "SSH 连接正常"
else
    echo_error "SSH 连接失败，请检查："
    echo "  1. 服务器 IP 是否正确"
    echo "  2. SSH 密钥是否配置"
    echo "  3. 防火墙是否开放 22 端口"
    exit 1
fi

# 2. 上传部署脚本
echo "上传部署脚本..."
scp deploy/auto_deploy.sh ${SERVER_USER}@${SERVER_IP}:/tmp/auto_deploy.sh
echo_step "脚本上传完成"

# 3. 执行部署
echo "执行远程部署..."
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
    chmod +x /tmp/auto_deploy.sh
    bash /tmp/auto_deploy.sh
ENDSSH

if [ $? -eq 0 ]; then
    echo_step "远程部署成功"
else
    echo_error "远程部署失败"
    exit 1
fi

# 4. 验证服务
echo "验证服务..."
HEALTH=$(curl -s http://${SERVER_IP}:8000/api/health)

if echo $HEALTH | grep -q "healthy"; then
    echo_step "服务健康检查通过"
    echo "服务状态：$HEALTH"
else
    echo_error "服务健康检查失败"
    exit 1
fi

echo ""
echo "========================================"
echo "🎉 远程部署完成！"
echo "========================================"
echo ""
echo "服务地址：http://${SERVER_IP}:8000"
echo "健康检查：http://${SERVER_IP}:8000/api/health"
echo ""
