#!/bin/bash
# AI Love World - 一键更新部署脚本（本地执行版）
# 版本：v2.2.1
# 用途：已有部署的服务器一键更新

set -e

echo "=========================================="
echo "🚀 AI Love World 一键更新部署"
echo "=========================================="
echo ""

# ============== 配置信息 ==============
DEPLOY_DIR="/var/www/ailoveworld"
REPO_URL="https://1129323634546582:pt-fqXLkLFxt0FtsZOrjMY4f35z_3ad4bc37-b332-4160-ba47-11c0d69b248f@codeup.aliyun.com/69a0572966d410a0f265834c/AILOVE1/AILOVE_V1.git"

# ============== 1. 停止服务 ==============
echo "📦 步骤 1/6: 停止现有服务..."
PIDS=$(ps aux | grep "uvicorn.*main:app" | grep -v grep | awk '{print $2}' || true)
if [ -n "$PIDS" ]; then
    echo "$PIDS" | xargs kill -15 2>/dev/null || true
    sleep 2
fi
echo "✅ 服务已停止"

# ============== 2. 拉取最新代码 ==============
echo "📦 步骤 2/6: 拉取最新代码..."
cd "$DEPLOY_DIR"

if [ -d ".git" ]; then
    # 已有 git 仓库，配置凭证后 pull
    git config credential.helper store
    echo "https://1129323634546582:pt-fqXLkLFxt0FtsZOrjMY4f35z_3ad4bc37-b332-4160-ba47-11c0d69b248f@codeup.aliyun.com" > ~/.git-credentials
    chmod 600 ~/.git-credentials
    git pull origin master
    echo "✅ 代码已更新"
else
    echo "❌ 错误：未找到 git 仓库，请使用完整部署脚本"
    exit 1
fi

# ============== 3. 执行数据库迁移 ==============
echo "📦 步骤 3/6: 执行数据库迁移..."
cd "$DEPLOY_DIR"
mkdir -p data

# 执行所有迁移（使用 IF NOT EXISTS，重复执行无害）
sqlite3 data/users.db < server/migration.sql 2>/dev/null && echo "  ✅ 基础表" || echo "  ⚠️  已存在"
sqlite3 data/users.db < server/migration_v2.sql 2>/dev/null && echo "  ✅ v2" || echo "  ⚠️  已存在"
sqlite3 data/users.db < server/migration_v3.sql 2>/dev/null && echo "  ✅ v3" || echo "  ⚠️  已存在"
sqlite3 data/users.db < server/migration_v4.sql 2>/dev/null && echo "  ✅ v4" || echo "  ⚠️  已存在"
sqlite3 data/users.db < server/migration_v5.sql 2>/dev/null && echo "  ✅ v5(积分)" || echo "  ⚠️  已存在"

echo "✅ 数据库迁移完成"

# ============== 4. 更新依赖 ==============
echo "📦 步骤 4/6: 更新 Python 依赖..."
cd "$DEPLOY_DIR"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    pip install -r requirements.txt -q
    echo "✅ 依赖已更新"
else
    echo "⚠️  未找到虚拟环境，跳过依赖更新"
fi

# ============== 5. 启动服务 ==============
echo "📦 步骤 5/6: 启动服务..."
cd "$DEPLOY_DIR/server"
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > ../server.log 2>&1 &
sleep 3
echo "✅ 服务已启动"

# ============== 6. 验证 ==============
echo "📦 步骤 6/6: 验证服务..."
sleep 2

if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
    echo "✅ 服务运行正常"
else
    echo "❌ 服务启动失败，查看日志：tail -f /var/www/ailoveworld/server.log"
    exit 1
fi

# ============== 完成 ==============
echo ""
echo "=========================================="
echo "🎉 更新部署完成！"
echo "=========================================="
echo ""
echo "📍 服务地址："
echo "   - 前端：http://您的服务器 IP/"
echo "   - API: http://您的服务器 IP:8000/"
echo ""
echo "📊 常用命令："
echo "   - 查看日志：tail -f /var/www/ailoveworld/server.log"
echo "   - 重启服务：bash /var/www/ailoveworld/deploy/update_and_deploy.sh"
echo ""
echo "🔒 本次更新内容（v2.2.1）："
echo "   ✅ 修复创建 AI 无法获取令牌"
echo "   ✅ 修复列表加载失败"
echo "   ✅ 修复管理后台加载失败"
echo "   ✅ 修复仪表盘数据为空"
echo "   ✅ 添加 GitHub OAuth 配置"
echo "   ✅ 删除重复建表代码"
echo "=========================================="
