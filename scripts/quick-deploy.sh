#!/bin/bash
# AI Love World - 快速部署脚本
# 版本：v2.1.0
# 用途：一键部署测试环境

set -e

echo "🚀 AI Love World 快速部署开始..."

# 配置
INSTALL_DIR="/var/www/ailoveworld"
PYTHON_VERSION="3.12"
DOMAIN="localhost"
PORT="8000"

# 1. 创建目录
echo "📁 创建目录..."
sudo mkdir -p $INSTALL_DIR
sudo chown $USER:$USER $INSTALL_DIR

# 2. 复制代码
echo "📦 复制代码..."
cd /home/admin/.openclaw/workspace/projects/ai-love-world
cp -r server/ $INSTALL_DIR/
cp -r web/ $INSTALL_DIR/ 2>/dev/null || true
cp requirements.txt $INSTALL_DIR/ 2>/dev/null || true
cp .env.example $INSTALL_DIR/.env 2>/dev/null || true

# 3. 创建虚拟环境
echo "🐍 创建 Python 虚拟环境..."
cd $INSTALL_DIR
python3 -m venv venv
source venv/bin/activate

# 4. 安装依赖
echo "📥 安装依赖..."
pip install -r requirements.txt 2>/dev/null || pip install fastapi uvicorn python-dotenv sqlite3

# 5. 初始化数据库
echo "💾 初始化数据库..."
mkdir -p data
python3 -c "
import sqlite3
conn = sqlite3.connect('data/users.db')
print('数据库创建成功')
conn.close()
"

# 6. 创建 .env 文件
echo "⚙️ 创建配置文件..."
cat > .env << EOF
DB_PATH=$INSTALL_DIR/data/users.db
DOMAIN=$DOMAIN
PORT=$PORT
ADMIN_PASSWORD=admin123
EOF

# 7. 启动服务
echo "🔥 启动服务..."
cd $INSTALL_DIR

# 停止旧进程
pkill -f "uvicorn server.main:app" 2>/dev/null || true
sleep 2

# 启动主服务
nohup venv/bin/uvicorn server.main:app --host 0.0.0.0 --port $PORT > logs/main.log 2>&1 &
echo "✅ 主服务已启动 (端口 $PORT)"

# 启动 Romance 服务
nohup venv/bin/uvicorn server.romance:app --host 0.0.0.0 --port 8004 > logs/romance.log 2>&1 &
echo "✅ Romance 服务已启动 (端口 8004)"

sleep 3

# 8. 检查服务状态
echo "🔍 检查服务状态..."
if curl -s http://localhost:$PORT/ > /dev/null; then
    echo "✅ 主服务运行正常"
else
    echo "❌ 主服务启动失败"
fi

if curl -s http://localhost:8004/ > /dev/null; then
    echo "✅ Romance 服务运行正常"
else
    echo "❌ Romance 服务启动失败"
fi

echo ""
echo "=========================================="
echo "🎉 部署完成！"
echo "=========================================="
echo "📍 服务地址：http://localhost:$PORT"
echo "💕 Romance API: http://localhost:8004"
echo "📊 文档地址：http://localhost:$PORT/docs"
echo "=========================================="
echo ""
echo "查看日志：tail -f $INSTALL_DIR/logs/*.log"
echo "停止服务：pkill -f 'uvicorn server'"
