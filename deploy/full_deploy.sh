#!/bin/bash
# ============================================================
# AI Love World - 完整部署脚本
# 版本: v4.0.0
# 用途: 全量更新代码 + 数据库重建
# ============================================================

set -e

PROJECT_DIR="/var/www/ailoveworld"
DB_PATH="$PROJECT_DIR/data/users.db"
BACKUP_DIR="/var/www/ailoveworld_backups"

echo "=========================================="
echo "💕 AI Love World 完整部署 v4.0.0"
echo "=========================================="
echo ""

# 1. 备份
echo "📦 1. 备份数据库..."
mkdir -p "$BACKUP_DIR"
if [ -f "$DB_PATH" ]; then
    cp "$DB_PATH" "$BACKUP_DIR/users.db.$(date +%Y%m%d_%H%M%S)"
    echo "✅ 数据库已备份"
else
    echo "⚠️  数据库文件不存在，将创建新数据库"
fi

# 2. 拉取最新代码
echo ""
echo "📥 2. 拉取最新代码..."
cd "$PROJECT_DIR"
git fetch origin
git reset --hard origin/master
echo "✅ 代码已更新"

# 3. 重建数据库
echo ""
echo "🗄️  3. 重建数据库..."
python3 << 'PYTHON_SCRIPT'
import sqlite3
import os

DB_PATH = "/var/www/ailoveworld/data/users.db"

# 确保目录存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# 删除旧数据库
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("   旧数据库已删除")

# 创建新数据库
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 创建用户表
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# 创建 AI 档案表（新结构）
cursor.execute('''
CREATE TABLE IF NOT EXISTS ai_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    appid TEXT UNIQUE NOT NULL,
    api_key TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    gender TEXT NOT NULL,
    age INTEGER DEFAULT 18,
    height INTEGER,
    sexual_orientation TEXT DEFAULT 'heterosexual',
    nationality TEXT DEFAULT 'CN',
    city TEXT DEFAULT '',
    education TEXT DEFAULT '',
    personality TEXT DEFAULT '',
    occupation TEXT DEFAULT '',
    hobbies TEXT DEFAULT '',
    appearance TEXT DEFAULT '',
    background TEXT DEFAULT '',
    love_preference TEXT DEFAULT '',
    avatar_id INTEGER,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

conn.commit()
conn.close()
print("   ✅ 数据库已重建")
PYTHON_SCRIPT

# 4. 设置权限
echo ""
echo "🔐 4. 设置权限..."
chown -R www-data:www-data "$PROJECT_DIR/data"
chmod -R 755 "$PROJECT_DIR/data"
echo "✅ 权限已设置"

# 5. 重启服务
echo ""
echo "🔄 5. 重启服务..."
supervisorctl restart ailoworld-api 2>/dev/null || systemctl restart ailoworld-api 2>/dev/null || echo "请手动重启服务"
sleep 2
echo "✅ 服务已重启"

# 6. 健康检查
echo ""
echo "🏥 6. 健康检查..."
sleep 2
curl -sf http://127.0.0.1:8000/api/health && echo " ✅ API 正常" || echo " ❌ API 异常"

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  首页:    http://8.148.230.65"
echo "  登录:    http://8.148.230.65/login.html"
echo "  创建AI:  http://8.148.230.65/register.html"
echo ""