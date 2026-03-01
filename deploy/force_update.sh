#!/bin/bash
# AI Love World - 强制部署脚本
# 确保 100% 更新到最新代码

echo "=========================================="
echo "AI Love World 强制部署"
echo "=========================================="

cd /var/www/ailoveworld

# 1. 停止服务
echo "1. 停止服务..."
supervisorctl stop ailoworld-api

# 2. 强制更新代码
echo "2. 强制更新代码..."
git fetch origin
git reset --hard origin/master
git pull origin master

# 3. 检查版本
echo "3. 检查版本..."
head -5 server/main.py

# 4. 重启服务
echo "4. 重启服务..."
supervisorctl start ailoworld-api

# 5. 等待启动
echo "5. 等待服务启动..."
sleep 3

# 6. 检查状态
echo "6. 检查服务状态..."
supervisorctl status ailoworld-api

# 7. 测试 API
echo "7. 测试 API..."
echo ""
echo "健康检查:"
curl -s http://localhost:8000/api/health
echo ""
echo ""
echo "管理后台用户列表:"
curl -s -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"admin_id":"1000000000","password":"admin123456"}' > /tmp/admin_login.json
ADMIN_TOKEN=$(cat /tmp/admin_login.json | grep -o '"token":"[^"]*"' | sed 's/"token":"//;s/"//')
curl -s "http://localhost:8000/api/admin/users?page=1&limit=50" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
echo ""

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="