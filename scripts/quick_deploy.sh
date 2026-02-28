#!/bin/bash
# AI Love World 快速部署脚本（简化版）
# 无需下载，直接 git clone

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 配置
PROJECT_DIR="/var/www/ailoveworld"
CODEUP_USER="1129323634546582"
CODEUP_TOKEN="pt-fqXLkLFxt0FtsZOrjMY4f35z_3ad4bc37-b332-4160-ba47-11c0d69b248f"
REPO_URL="https://codeup.aliyun.com/69a0572966d410a0f265834c/AILOVE1/AILOVE_V1.git"

print_info "=========================================="
print_info "AI Love World 快速部署"
print_info "=========================================="

# 检查 root
if [ "$EUID" -ne 0 ]; then
    print_error "请使用 sudo 运行"
    exit 1
fi

# 安装依赖
print_info "安装系统依赖..."
apt update
apt install -y python3-pip python3-venv nginx git curl

# 创建目录
print_info "创建目录..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 配置 Git 凭证
print_info "配置 Git 凭证..."
git config --global credential.helper store
echo "https://${CODEUP_USER}:${CODEUP_TOKEN}@codeup.aliyun.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# 克隆代码
print_info "克隆代码..."
git clone $REPO_URL .

# 创建虚拟环境
print_info "创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# 安装依赖
print_info "安装 Python 依赖..."
pip install -r server/requirements.txt

# 创建数据目录
mkdir -p /var/www/ailoveworld/data
mkdir -p /var/www/ailoveworld/logs

# 创建 .env 文件
print_info "创建环境变量..."
cat > .env << EOF
DB_PATH=/var/www/ailoveworld/data/users.db
JWT_SECRET=$(openssl rand -hex 32)
ADMIN_PASSWORD=$(openssl rand -base64 16)
SERVER_URL=http://127.0.0.1:8000
EOF

chmod 600 .env

print_success "=========================================="
print_success "基础部署完成！"
print_success "=========================================="
print_info ""
print_info "下一步："
print_info "1. 编辑 .env 文件配置 GitHub OAuth"
print_info "2. 运行服务：cd /var/www/ailoveworld && source venv/bin/activate && uvicorn server.main:app --host 0.0.0.0 --port 8000"
print_info "3. 查看完整文档：docs/DEPLOY.md"
print_info ""
