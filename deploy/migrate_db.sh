#!/bin/bash
# AI Love World 数据库迁移脚本
# 解决 birth_date -> age 字段变更

set -e

echo "=========================================="
echo "AI Love World 数据库迁移"
echo "=========================================="

DB_PATH="${DB_PATH:-/var/www/ailoveworld/data/users.db}"

if [ ! -f "$DB_PATH" ]; then
    echo "❌ 数据库文件不存在: $DB_PATH"
    exit 1
fi

# 备份数据库
BACKUP_PATH="${DB_PATH}.backup_$(date +%Y%m%d_%H%M%S)"
cp "$DB_PATH" "$BACKUP_PATH"
echo "✅ 数据库已备份: $BACKUP_PATH"

# 检查表结构
echo ""
echo "📋 检查表结构..."

# 执行迁移
sqlite3 "$DB_PATH" << 'EOF'
-- 检查是否有 birth_date 字段
.mode column
.headers on

-- 先检查表结构
.schema ai_profiles

-- 添加 age 字段（如果不存在）
ALTER TABLE ai_profiles ADD COLUMN age INTEGER DEFAULT 18;

-- 添加 sexual_orientation 字段（如果不存在）
ALTER TABLE ai_profiles ADD COLUMN sexual_orientation TEXT DEFAULT 'heterosexual';

-- 从 birth_date 计算年龄（如果有 birth_date 字段）
-- UPDATE ai_profiles SET age = CAST((strftime('%Y', 'now') - strftime('%Y', birth_date)) AS INTEGER) WHERE birth_date IS NOT NULL AND age IS NULL;

.quit
EOF

echo ""
echo "✅ 迁移完成！"
echo ""
echo "请重启服务: supervisorctl restart ailoworld-api"