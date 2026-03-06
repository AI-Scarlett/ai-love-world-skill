#!/bin/bash
# AI Love World - 修复全局配置 API 冲突
# 版本：v2.2.1
# 用途：删除重复的 global_settings_api.py，解决路由冲突

set -e

echo "=========================================="
echo "🔧 修复全局配置 API 冲突"
echo "=========================================="
echo ""

DEPLOY_DIR="/var/www/ailoveworld"

# 1. 停止服务
echo "📦 步骤 1/4: 停止服务..."
ps aux | grep "uvicorn.*main:app" | grep -v grep | awk '{print $2}' | xargs kill -15 2>/dev/null || true
sleep 2
echo "✅ 服务已停止"

# 2. 删除重复的 API 文件
echo "📦 步骤 2/4: 删除重复的 API 文件..."
cd "$DEPLOY_DIR/server"
if [ -f "global_settings_api.py" ]; then
    rm -f global_settings_api.py
    echo "✅ 已删除 global_settings_api.py"
else
    echo "⚠️  global_settings_api.py 不存在"
fi

# 3. 拉取最新代码（确保 main.py 是最新的）
echo "📦 步骤 3/4: 拉取最新代码..."
cd "$DEPLOY_DIR"
git pull origin master
echo "✅ 代码已更新"

# 4. 启动服务
echo "📦 步骤 4/4: 启动服务..."
cd "$DEPLOY_DIR/server"
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > ../server.log 2>&1 &
sleep 3
echo "✅ 服务已启动"

# 验证
echo ""
echo "🔍 验证服务..."
if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
    echo "✅ 服务运行正常"
else
    echo "❌ 服务启动失败"
fi

# 测试全局配置 API
echo ""
echo "🔍 测试全局配置 API..."
RESULT=$(curl -s http://localhost:8000/api/admin/global-settings)
if echo "$RESULT" | grep -q "success"; then
    echo "✅ 全局配置 API 正常"
    echo "   返回：$RESULT"
else
    echo "❌ 全局配置 API 异常"
    echo "   返回：$RESULT"
fi

echo ""
echo "=========================================="
echo "🎉 修复完成！"
echo "=========================================="
echo ""
echo "问题原因：global_settings_api.py 与 main.py 中的路由重复"
echo "解决方案：删除 global_settings_api.py，统一使用 main.py 中的 API"
echo ""
