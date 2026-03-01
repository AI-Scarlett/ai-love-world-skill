#!/bin/bash
# AI Love World - 代码更新脚本
# 适用：已部署的服务器
# 作者：丝佳丽 💋

set -e

echo "=========================================="
echo "💕 AI Love World 代码更新"
echo "作者：丝佳丽 💋"
echo "=========================================="
echo ""

# 项目目录
PROJECT_DIR="/var/www/ailoveworld"

# 检查目录是否存在
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 项目目录不存在：$PROJECT_DIR"
    echo "请先运行 deploy/quick_deploy.sh 进行初次部署"
    exit 1
fi

cd $PROJECT_DIR

echo "📦 1. 备份当前代码..."
BACKUP_DIR="/var/www/ailoveworld_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp -r $PROJECT_DIR/* $BACKUP_DIR/ 2>/dev/null || true
echo "✅ 备份完成：$BACKUP_DIR"

echo ""
echo "📥 2. 拉取最新代码..."
git fetch origin
git reset --hard origin/master
echo "✅ 代码已更新到最新版本"

echo ""
echo "🐍 3. 更新 Python 依赖..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q 2>/dev/null || pip install fastapi uvicorn httpx pyjwt python-dotenv cryptography dashscope -q
echo "✅ 依赖更新完成"

echo ""
echo "🔄 4. 重启服务..."
supervisorctl restart ailoworld-api
supervisorctl restart ailoworld-auth
echo "✅ 服务已重启"

echo ""
echo "📊 5. 检查服务状态..."
sleep 2
supervisorctl status

echo ""
echo "=========================================="
echo "✅ 更新完成！"
echo "=========================================="
echo ""
echo "📋 测试访问："
echo "   http://你的服务器IP"
echo "   http://你的服务器IP/api/health"
echo ""
echo "📝 查看日志："
echo "   tail -f /var/log/ailoveworld/api.log"
echo ""
echo "🔄 如需回滚："
echo "   rm -rf /var/www/ailoveworld/*"
echo "   cp -r $BACKUP_DIR/* /var/www/ailoveworld/"
echo "   supervisorctl restart all"
echo ""
echo "💋 丝佳丽祝您更新顺利！"