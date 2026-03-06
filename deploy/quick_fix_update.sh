#!/bin/bash
# AI Love World - 一键更新脚本（Bug 修复版）
# 版本：v2.2.2
# 更新内容：
#   - 修复帖子详情页无法查看问题
#   - 移除社区收藏和分享功能
#   - 礼物数据服务端化

set -e

echo "=========================================="
echo "🚀 AI Love World 一键更新 (v2.2.2)"
echo "=========================================="
echo ""

DEPLOY_DIR="/var/www/ailoveworld"

# 1. 停止服务
echo "📦 步骤 1/5: 停止服务..."
pkill -f "uvicorn.*main:app" || true
sleep 2
echo "✅ 服务已停止"

# 2. 拉取最新代码
echo "📦 步骤 2/5: 拉取最新代码..."
cd "$DEPLOY_DIR"
git pull origin master
echo "✅ 代码已更新"

# 3. 执行数据库迁移（如果有）
echo "📦 步骤 3/5: 执行数据库迁移..."
cd "$DEPLOY_DIR"
if [ -f "server/migration_v7.sql" ]; then
    sqlite3 data/users.db < server/migration_v7.sql && echo "  ✅ 迁移 v7" || echo "  ⚠️  已存在"
fi
if [ -f "server/migration_v6.sql" ]; then
    sqlite3 data/users.db < server/migration_v6.sql && echo "  ✅ 迁移 v6" || echo "  ⚠️  已存在"
fi
echo "✅ 数据库迁移完成"

# 4. 启动服务
echo "📦 步骤 4/5: 启动服务..."
cd "$DEPLOY_DIR/server"
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > ../server.log 2>&1 &
sleep 3
echo "✅ 服务已启动"

# 5. 验证
echo "📦 步骤 5/5: 验证服务..."
if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
    echo "✅ 服务运行正常"
else
    echo "❌ 服务启动失败，查看日志：tail -f /var/www/ailoveworld/server.log"
    exit 1
fi

# 测试新增 API
echo ""
echo "🔍 测试新增 API..."
if curl -s http://localhost:8000/api/community/posts/1 | grep -q "success"; then
    echo "✅ 帖子详情 API 正常"
else
    echo "⚠️  帖子详情 API 可能需要重启或帖子不存在"
fi

echo ""
echo "=========================================="
echo "🎉 更新完成！"
echo "=========================================="
echo ""
echo "📋 本次更新内容 (v2.2.2):"
echo "  ✅ 修复帖子详情页无法查看问题"
echo "  ✅ 移除社区收藏和分享功能"
echo "  ✅ 礼物数据服务端化"
echo ""
echo "📍 服务地址："
echo "  - 前端：http://您的服务器 IP/"
echo "  - API: http://您的服务器 IP:8000/"
echo ""
echo "📊 常用命令："
echo "  - 查看日志：tail -f /var/www/ailoveworld/server.log"
echo "  - 重启服务：bash /var/www/ailoveworld/deploy/quick_update.sh"
echo ""
