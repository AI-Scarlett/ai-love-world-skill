#!/bin/bash
# AI Love World 快速部署脚本（当前目录版）
# 在已有的代码目录中直接运行

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

print_info "=========================================="
print_info "AI Love World 快速部署（当前目录）"
print_info "=========================================="

# 检查 root
if [ "$EUID" -ne 0 ]; then
    print_error "请使用 sudo 运行"
    exit 1
fi

# 检查是否在正确目录
if [ ! -f "server/main.py" ]; then
    print_error "请在项目根目录运行此脚本"
    print_error "当前目录缺少 server/main.py"
    exit 1
fi

print_info "当前目录：$(pwd)"

# 安装依赖
print_info "安装系统依赖..."
apt update
apt install -y python3-pip python3-venv nginx git curl

# 创建虚拟环境
print_info "创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
else
    print_info "虚拟环境已存在，跳过"
fi

source venv/bin/activate
pip install --upgrade pip

# 安装 Python 依赖
print_info "安装 Python 依赖..."
if [ -f "server/requirements.txt" ]; then
    pip install -r server/requirements.txt
fi

# 创建数据目录
print_info "创建数据目录..."
mkdir -p data logs
mkdir -p /var/www/ailoveworld/data
mkdir -p /var/www/ailoveworld/logs

# 创建 .env 文件
print_info "创建环境变量..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
DB_PATH=/var/www/ailoveworld/data/users.db
JWT_SECRET=$(openssl rand -hex 32)
ADMIN_PASSWORD=$(openssl rand -base64 16)
SERVER_URL=http://127.0.0.1:8000
EOF
    chmod 600 .env
    print_success ".env 文件已创建"
else
    print_info ".env 文件已存在，跳过"
fi

# 配置 Nginx
print_info "配置 Nginx..."
PROJECT_DIR=$(pwd)
cat > /etc/nginx/sites-available/ailoveworld << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        root $PROJECT_DIR/web;
        try_files \$uri \$uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    access_log $PROJECT_DIR/logs/nginx_access.log;
    error_log $PROJECT_DIR/logs/nginx_error.log;
}
EOF

ln -sf /etc/nginx/sites-available/ailoveworld /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

print_success "=========================================="
print_success "部署完成！"
print_success "=========================================="
print_info ""
print_info "启动服务："
print_info "  source venv/bin/activate"
print_info "  uvicorn server.main:app --host 0.0.0.0 --port 8000 &"
print_info ""
print_info "查看 .env 获取管理员密码："
print_info "  cat .env | grep ADMIN_PASSWORD"
print_info ""
