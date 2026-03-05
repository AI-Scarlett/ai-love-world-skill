#!/bin/bash
# AI Love World - 完整重置部署脚本
# 版本：v2.1.0
# 用途：阿里云 ECS 重置后一键部署

set -e

echo "=========================================="
echo "🚀 AI Love World 完整部署开始"
echo "=========================================="
echo ""

# ============== 1. 系统更新 ==============
echo "📦 步骤 1/8: 更新系统..."
sudo apt update -y
sudo apt upgrade -y

# ============== 2. 安装依赖 ==============
echo "📦 步骤 2/8: 安装系统依赖..."
sudo apt install -y git curl wget nginx python3 python3-pip python3-venv supervisor

# ============== 3. 创建目录 ==============
echo "📁 步骤 3/8: 创建目录..."
sudo mkdir -p /var/www/ailoveworld
sudo chown $USER:$USER /var/www/ailoveworld

# ============== 4. 克隆代码 ==============
echo "📦 步骤 4/8: 克隆代码..."
cd /tmp
rm -rf ailoveworld
git clone https://codeup.aliyun.com/69a0572966d410a0f265834c/AILOVE1/AILOVE_V1.git ailoveworld
cd ailoveworld

# ============== 5. 复制代码 ==============
echo "📦 步骤 5/8: 复制代码到部署目录..."
cp -r server/ /var/www/ailoveworld/
cp -r web/ /var/www/ailoveworld/ 2>/dev/null || true
cp requirements.txt /var/www/ailoveworld/
cp .env.example /var/www/ailoveworld/.env

# ============== 6. 创建虚拟环境 ==============
echo "🐍 步骤 6/8: 创建 Python 虚拟环境..."
cd /var/www/ailoveworld
python3 -m venv venv
source venv/bin/activate

# ============== 7. 安装依赖 ==============
echo "📥 步骤 7/8: 安装 Python 依赖..."
pip install -r requirements.txt

# ============== 8. 初始化数据库 ==============
echo "💾 初始化数据库..."
mkdir -p data
python3 -c "
import sqlite3
conn = sqlite3.connect('data/users.db')
print('✅ 数据库创建成功')
conn.close()
"

# ============== 9. 配置 Supervisor ==============
echo "⚙️ 配置 Supervisor..."
sudo tee /etc/supervisor/conf.d/ailoveworld.conf > /dev/null << 'EOF'
[program:ailoworld-main]
command=/var/www/ailoveworld/venv/bin/uvicorn server.main:app --host 0.0.0.0 --port 8000
directory=/var/www/ailoveworld
autostart=true
autorestart=true
stderr_logfile=/var/www/ailoveworld/logs/main.err.log
stdout_logfile=/var/www/ailoveworld/logs/main.out.log

[program:ailoworld-romance]
command=/var/www/ailoveworld/venv/bin/uvicorn server.romance:app --host 0.0.0.0 --port 8004
directory=/var/www/ailoveworld
autostart=true
autorestart=true
stderr_logfile=/var/www/ailoveworld/logs/romance.err.log
stdout_logfile=/var/www/ailoveworld/logs/romance.out.log
EOF

# ============== 10. 配置 Nginx ==============
echo "⚙️ 配置 Nginx..."
sudo tee /etc/nginx/sites-available/ailoveworld > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    
    # 静态文件
    location / {
        root /var/www/ailoveworld/web;
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 日志
    access_log /var/www/ailoveworld/logs/nginx_access.log;
    error_log /var/www/ailoveworld/logs/nginx_error.log;
}
EOF

# 启用站点
sudo ln -sf /etc/nginx/sites-available/ailoveworld /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 测试并重载
sudo nginx -t
sudo nginx -s reload 2>/dev/null || sudo systemctl restart nginx

# ============== 11. 启动服务 ==============
echo "🔥 步骤 8/8: 启动服务..."

# 创建日志目录
mkdir -p logs

# 更新 Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start ailoworld-main
sudo supervisorctl start ailoworld-romance

# 等待启动
sleep 5

# ============== 12. 验证 ==============
echo ""
echo "🔍 验证服务状态..."

# 检查主服务
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ 主服务运行正常 (端口 8000)"
else
    echo "❌ 主服务启动失败"
fi

# 检查 Romance 服务
if curl -s http://localhost:8004/ > /dev/null; then
    echo "✅ Romance 服务运行正常 (端口 8004)"
else
    echo "❌ Romance 服务启动失败"
fi

# 检查 Nginx
if curl -s http://localhost/ > /dev/null; then
    echo "✅ Nginx 运行正常 (端口 80)"
else
    echo "❌ Nginx 启动失败"
fi

# ============== 完成 ==============
echo ""
echo "=========================================="
echo "🎉 部署完成！"
echo "=========================================="
echo "📍 服务地址："
echo "   - 前端：http://localhost/"
echo "   - API: http://localhost:8000/"
echo "   - Romance API: http://localhost:8004/"
echo "   - 文档：http://localhost/docs"
echo ""
echo "📊 服务管理："
echo "   - 查看状态：supervisorctl status"
echo "   - 重启服务：supervisorctl restart ailoworld:*"
echo "   - 查看日志：tail -f /var/www/ailoveworld/logs/*.log"
echo ""
echo "🔒 安全组配置："
echo "   请在阿里云控制台开放以下端口："
echo "   - 80 (HTTP)"
echo "   - 443 (HTTPS, 可选)"
echo "   - 8000-8006 (API 端口)"
echo "=========================================="
echo ""
