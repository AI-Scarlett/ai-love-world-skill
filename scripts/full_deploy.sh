#!/bin/bash
# AI Love World 完整重新部署脚本
# 版本：v2.0.0

set -e

echo "=========================================="
echo "AI Love World 完整重新部署"
echo "=========================================="

# 配置
PROJECT_DIR="/var/www/ailoveworld"
CODEUP_USER="1129323634546582"
CODEUP_TOKEN="pt-fqXLkLFxt0FtsZOrjMY4f35z_3ad4bc37-b332-4160-ba47-11c0d69b248f"
REPO_URL="https://codeup.aliyun.com/69a0572966d410a0f265834c/AILOVE1/AILOVE_V1.git"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 1. 停止所有服务
print_info "停止所有服务..."
pkill -9 -f uvicorn || true
sleep 2

# 2. 备份旧代码
print_info "备份旧代码..."
if [ -d "$PROJECT_DIR" ]; then
    mv $PROJECT_DIR ${PROJECT_DIR}.backup.$(date +%Y%m%d_%H%M%S)
fi

# 3. 创建目录
print_info "创建目录..."
mkdir -p $PROJECT_DIR
mkdir -p $PROJECT_DIR/{data,logs}
cd $PROJECT_DIR

# 4. 配置 Git 凭证
print_info "配置 Git 凭证..."
git config --global credential.helper store
echo "https://${CODEUP_USER}:${CODEUP_TOKEN}@codeup.aliyun.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# 5. 克隆最新代码
print_info "克隆最新代码..."
git clone $REPO_URL .

# 6. 创建虚拟环境
print_info "创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# 7. 安装依赖
print_info "安装 Python 依赖..."
pip install -r server/requirements.txt

# 8. 创建 .env 文件
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
    print_info "管理员密码：$(grep ADMIN_PASSWORD .env | cut -d= -f2)"
fi

# 9. 配置 Nginx
print_info "配置 Nginx..."
cat > /etc/nginx/sites-available/ailoveworld << 'EOF'
server {
    listen 80;
    server_name _;
    
    # 静态文件
    location / {
        root /var/www/ailoveworld/web;
        try_files $uri $uri/ /index.html;
    }
    
    # 主 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # 管理后台 API
    location /api/admin/ {
        proxy_pass http://127.0.0.1:8005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    access_log /var/log/nginx/ailoveworld_access.log;
    error_log /var/log/nginx/ailoveworld_error.log;
}
EOF

ln -sf /etc/nginx/sites-available/ailoveworld /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

print_success "Nginx 配置完成"

# 10. 启动所有服务
print_info "启动所有服务..."

nohup uvicorn server.main:app --host 0.0.0.0 --port 8000 > logs/main.log 2>&1 &
nohup uvicorn server.auth:app --host 0.0.0.0 --port 8002 > logs/auth.log 2>&1 &
nohup uvicorn server.user:app --host 0.0.0.0 --port 8001 > logs/user.log 2>&1 &
nohup uvicorn server.wallet:app --host 0.0.0.0 --port 8003 > logs/wallet.log 2>&1 &
nohup uvicorn server.romance:app --host 0.0.0.0 --port 8004 > logs/romance.log 2>&1 &
nohup uvicorn server.admin:app --host 0.0.0.0 --port 8005 > logs/admin.log 2>&1 &
nohup uvicorn server.skill_auth:app --host 0.0.0.0 --port 8006 > logs/skill.log 2>&1 &

sleep 5

# 11. 验证服务
print_info "验证服务..."
echo ""
echo "=== 服务状态 ==="
ps aux | grep uvicorn | grep -v grep | wc -l
echo "个服务正在运行"

echo ""
echo "=== 端口监听 ==="
netstat -tulpn | grep -E '8000|8001|8002|8003|8004|8005|8006'

echo ""
echo "=== API 测试 ==="
curl -s http://localhost:8000/api/health
echo ""
curl -s http://localhost:8005/
echo ""

# 12. 显示访问信息
print_success "=========================================="
print_success "部署完成！"
print_success "=========================================="
echo ""
print_info "访问地址："
echo "  首页：http://$(hostname -I | awk '{print $1}')/"
echo "  管理后台：http://$(hostname -I | awk '{print $1}')/admin.html"
echo ""
print_info "管理员登录信息："
echo "  管理员 ID: 1000000000"
echo "  密码：$(grep ADMIN_PASSWORD .env | cut -d= -f2)"
echo ""
print_info "日志文件："
echo "  tail -f logs/main.log"
echo "  tail -f logs/admin.log"
echo ""
print_info "服务管理："
echo "  停止：pkill -f uvicorn"
echo "  重启：./restart.sh"
echo ""
