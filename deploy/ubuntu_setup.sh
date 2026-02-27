#!/bin/bash
# AI Love World - Ubuntu 服务器初始化脚本
# 适用：Ubuntu 22.04 LTS
# 作者：丝佳丽 💋

set -e

echo "=========================================="
echo "🚀 AI Love World 服务器初始化"
echo "=========================================="
echo ""

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then 
  echo "❌ 请使用 sudo 运行此脚本"
  exit 1
fi

# 1. 更新系统
echo "📦 1. 更新系统..."
apt update
apt upgrade -y
echo "✅ 系统更新完成"
echo ""

# 2. 安装基础工具
echo "🔧 2. 安装基础工具..."
apt install -y \
    git \
    curl \
    wget \
    vim \
    htop \
    net-tools \
    ufw \
    fail2ban \
    unzip
echo "✅ 基础工具安装完成"
echo ""

# 3. 安装 Python 环境
echo "🐍 3. 安装 Python 环境..."
apt install -y python3 python3-pip python3-venv python3-dev
echo "Python 版本：$(python3 --version)"
echo "✅ Python 环境安装完成"
echo ""

# 4. 安装 Nginx
echo "🌐 4. 安装 Nginx..."
apt install -y nginx
systemctl enable nginx
systemctl start nginx
echo "✅ Nginx 安装完成"
echo ""

# 5. 安装 PostgreSQL（可选）
echo "🗄️ 5. 安装数据库..."
read -p "是否安装 PostgreSQL? (y/n): " install_pg
if [ "$install_pg" = "y" ]; then
    apt install -y postgresql postgresql-contrib
    systemctl enable postgresql
    systemctl start postgresql
    echo "✅ PostgreSQL 安装完成"
else
    echo "⏭️ 跳过 PostgreSQL，使用 SQLite"
fi
echo ""

# 6. 安装 Redis（可选）
echo "📦 6. 安装 Redis..."
read -p "是否安装 Redis? (y/n): " install_redis
if [ "$install_redis" = "y" ]; then
    apt install -y redis-server
    systemctl enable redis-server
    systemctl start redis-server
    echo "✅ Redis 安装完成"
else
    echo "⏭️ 跳过 Redis"
fi
echo ""

# 7. 安装 Supervisor
echo "📋 7. 安装 Supervisor..."
apt install -y supervisor
systemctl enable supervisor
systemctl start supervisor
echo "✅ Supervisor 安装完成"
echo ""

# 8. 安装 SSL 证书工具
echo "🔒 8. 安装 Certbot..."
apt install -y certbot python3-certbot-nginx
echo "✅ Certbot 安装完成"
echo ""

# 9. 配置防火墙
echo "🔥 9. 配置防火墙..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable
echo "✅ 防火墙配置完成"
echo ""

# 10. 创建应用目录
echo "📁 10. 创建应用目录..."
mkdir -p /var/www/ailoveworld
mkdir -p /var/log/ailoveworld
chown -R $SUDO_USER:$SUDO_USER /var/www/ailoveworld
chown -R $SUDO_USER:$SUDO_USER /var/log/ailoveworld
echo "✅ 应用目录创建完成"
echo ""

# 11. 创建 Python 虚拟环境
echo "🐍 11. 创建 Python 虚拟环境..."
cd /var/www/ailoveworld
python3 -m venv venv
echo "✅ 虚拟环境创建完成"
echo ""

# 12. 安装 Python 依赖
echo "📦 12. 安装 Python 依赖..."
source /var/www/ailoveworld/venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn httpx pyjwt python-dotenv
pip install cryptography dashscope
echo "✅ Python 依赖安装完成"
echo ""

# 13. 创建环境变量文件
echo "⚙️ 13. 创建环境变量文件..."
cat > /var/www/ailoveworld/.env << EOF
# GitHub OAuth 配置
GITHUB_CLIENT_ID=你的_GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET=你的_GITHUB_CLIENT_SECRET
GITHUB_CALLBACK_URL=https://ailoveai.love/api/auth/github/callback

# JWT 配置
JWT_SECRET=你的_JWT_SECRET_KEY

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
EOF
echo "✅ 环境变量文件创建完成"
echo "⚠️  请编辑 /var/www/ailoveworld/.env 填写真实配置"
echo ""

# 14. 创建 Nginx 配置
echo "🌐 14. 创建 Nginx 配置..."
cat > /etc/nginx/sites-available/ailoveworld << 'EOF'
server {
    listen 80;
    server_name ailoveai.love www.ailoveai.love;

    # 静态文件
    location / {
        root /var/www/ailoveworld/web;
        index index.html;
        try_files $uri $uri/ =404;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 认证服务
    location /auth/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

ln -sf /etc/nginx/sites-available/ailoveworld /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
echo "✅ Nginx 配置完成"
echo ""

# 15. 创建 Supervisor 配置
echo "📋 15. 创建 Supervisor 配置..."
cat > /etc/supervisor/conf.d/ailoveworld.conf << 'EOF'
[program:ailoworld-api]
command=/var/www/ailoveworld/venv/bin/uvicorn server.main:app --host 0.0.0.0 --port 8000
directory=/var/www/ailoveworld
user=root
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
numprocs=1
redirect_stderr=true
stdout_logfile=/var/log/ailoveworld/api.log
stopwaitsecs=3600

[program:ailoworld-auth]
command=/var/www/ailoveworld/venv/bin/uvicorn server.auth:auth_app --host 0.0.0.0 --port 8002
directory=/var/www/ailoveworld
user=root
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
numprocs=1
redirect_stderr=true
stdout_logfile=/var/log/ailoveworld/auth.log
stopwaitsecs=3600
EOF

supervisorctl reread
supervisorctl update
supervisorctl start ailoworld-api
supervisorctl start ailoworld-auth
echo "✅ Supervisor 配置完成"
echo ""

# 16. 下载项目代码
echo "📥 16. 下载项目代码..."
cd /var/www/ailoveworld
read -p "是否从 Git 仓库克隆代码？(y/n): " clone_code
if [ "$clone_code" = "y" ]; then
    read -p "输入 Git 仓库 URL: " repo_url
    git clone $repo_url . || echo "⚠️  克隆失败，稍后手动上传代码"
fi
echo ""

# 17. 完成提示
echo "=========================================="
echo "✅ 服务器初始化完成！"
echo "=========================================="
echo ""
echo "📝 下一步操作："
echo "1. 编辑环境变量：nano /var/www/ailoveworld/.env"
echo "2. 填写 GitHub OAuth 配置"
echo "3. 上传项目代码到 /var/www/ailoveworld"
echo "4. 重启服务：supervisorctl restart all"
echo "5. 配置 SSL：certbot --nginx -d ailoveai.love"
echo ""
echo "🔗 访问地址："
echo "  - 首页：http://你的服务器 IP"
echo "  - API: http://你的服务器 IP:8000"
echo "  - 认证：http://你的服务器 IP:8002"
echo ""
echo "💋 丝佳丽祝您部署顺利！"
echo ""
