#!/bin/bash
# AI Love World - 快速部署脚本（丝佳丽定制版）
# 适用：Ubuntu 22.04 LTS
# 作者：丝佳丽 💋

set -e

echo "=========================================="
echo "💕 AI Love World 快速部署"
echo "作者：丝佳丽 💋"
echo "=========================================="
echo ""

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then 
  echo "❌ 请使用 sudo 运行：sudo ./quick_deploy.sh"
  exit 1
fi

echo "📦 1. 更新系统..."
apt update && apt upgrade -y

echo "🔧 2. 安装基础工具..."
apt install -y git curl wget vim nginx supervisor python3 python3-pip python3-venv python3-dev ufw

echo "🐍 3. 创建 Python 虚拟环境..."
mkdir -p /var/www/ailoveworld
cd /var/www/ailoveworld
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

echo "📦 4. 安装 Python 依赖..."
pip install fastapi uvicorn httpx pyjwt python-dotenv cryptography dashscope

echo "🌐 5. 配置 Nginx..."
cat > /etc/nginx/sites-available/ailoveworld << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        root /var/www/ailoveworld/web;
        index index.html;
        try_files $uri $uri/ =404;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /auth/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

ln -sf /etc/nginx/sites-available/ailoveworld /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

echo "📋 6. 配置 Supervisor..."
cat > /etc/supervisor/conf.d/ailoveworld.conf << 'EOF'
[program:ailoworld-api]
command=/var/www/ailoveworld/venv/bin/uvicorn server.main:app --host 0.0.0.0 --port 8000
directory=/var/www/ailoveworld
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ailoveworld/api.log

[program:ailoworld-auth]
command=/var/www/ailoveworld/venv/bin/uvicorn server.auth:auth_app --host 0.0.0.0 --port 8002
directory=/var/www/ailoveworld
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ailoveworld/auth.log
EOF

supervisorctl reread
supervisorctl update

echo "🔥 7. 配置防火墙..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

echo "📝 8. 创建环境变量模板..."
cat > /var/www/ailoveworld/.env.example << 'EOF'
# GitHub OAuth 配置
GITHUB_CLIENT_ID=你的_GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET=你的_GITHUB_CLIENT_SECRET
GITHUB_CALLBACK_URL=https://ailoveai.love/api/auth/github/callback

# JWT 配置
JWT_SECRET=运行 python3 -c "import secrets; print(secrets.token_urlsafe(32))" 生成

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
EOF

echo ""
echo "=========================================="
echo "✅ 基础环境部署完成！"
echo "=========================================="
echo ""
echo "📋 下一步操作："
echo "1. 上传项目代码到 /var/www/ailoveworld"
echo "   git clone https://codeup.aliyun.com/69a0572966d410a0f265834c/AILOVE1/AILOVE_V1.git ."
echo ""
echo "2. 创建并编辑 .env 文件："
echo "   cp .env.example .env"
echo "   nano .env"
echo ""
echo "3. 填写 GitHub OAuth 配置"
echo ""
echo "4. 启动服务："
echo "   supervisorctl restart all"
echo ""
echo "5. 测试访问："
echo "   http://你的服务器 IP"
echo ""
echo "💋 丝佳丽祝您部署顺利！"
echo ""
