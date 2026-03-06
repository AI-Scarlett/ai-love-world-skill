#!/bin/bash
# AI Love World - 查看错误日志并修复
# 版本：v2.2.1

echo "=========================================="
echo "🔍 查看服务器错误日志"
echo "=========================================="
echo ""

# 显示最新 100 行日志
echo "📋 最新日志 (最后 100 行):"
tail -100 /var/www/ailoveworld/server.log

echo ""
echo "=========================================="
echo "🔍 查找错误关键词:"
echo "=========================================="
echo ""

# 查找错误
grep -i "error\|exception\|traceback" /var/www/ailoveworld/server.log | tail -20

echo ""
echo "=========================================="
echo "📊 数据库表检查:"
echo "=========================================="
echo ""

# 检查数据库表
sqlite3 /var/www/ailoveworld/data/users.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"

echo ""
echo "=========================================="
echo "🔧 建议操作:"
echo "=========================================="
echo ""
echo "如果日志显示表不存在，执行:"
echo "  cd /var/www/ailoveworld"
echo "  sqlite3 data/users.db < server/migration_v2.sql"
echo "  sqlite3 data/users.db < server/migration_v3.sql"
echo "  sqlite3 data/users.db < server/migration_v5.sql"
echo ""
echo "然后重启服务:"
echo "  pkill -f uvicorn"
echo "  cd server && nohup uvicorn main:app --host 0.0.0.0 --port 8000 > ../server.log 2>&1 &"
echo ""
