#!/usr/bin/env python3
"""
AI Love World 数据库迁移脚本
解决 birth_date -> age 字段变更
"""

import sqlite3
import os
import sys
from datetime import datetime

# 数据库路径
DB_PATH = os.environ.get('DB_PATH', '/var/www/ailoveworld/data/users.db')

def main():
    print("=" * 50)
    print("AI Love World 数据库迁移")
    print("=" * 50)
    print()
    
    # 检查数据库文件
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        sys.exit(1)
    
    # 备份数据库
    backup_path = f"{DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import shutil
    shutil.copy(DB_PATH, backup_path)
    print(f"✅ 数据库已备份: {backup_path}")
    print()
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取表结构
    print("📋 检查表结构...")
    cursor.execute("PRAGMA table_info(ai_profiles)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    print(f"   现有字段: {list(columns.keys())}")
    print()
    
    # 添加缺失的字段
    migrations = []
    
    if 'age' not in columns:
        migrations.append("ALTER TABLE ai_profiles ADD COLUMN age INTEGER DEFAULT 18")
        print("   ➕ 添加 age 字段")
    
    if 'sexual_orientation' not in columns:
        migrations.append("ALTER TABLE ai_profiles ADD COLUMN sexual_orientation TEXT DEFAULT 'heterosexual'")
        print("   ➕ 添加 sexual_orientation 字段")
    
    if not migrations:
        print("✅ 数据库已是最新结构，无需迁移")
        conn.close()
        return
    
    # 执行迁移
    print()
    print("🔄 执行迁移...")
    for sql in migrations:
        try:
            cursor.execute(sql)
            print(f"   ✅ {sql}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"   ⚠️  字段已存在，跳过")
            else:
                print(f"   ❌ 错误: {e}")
    
    conn.commit()
    conn.close()
    
    print()
    print("=" * 50)
    print("✅ 迁移完成！")
    print("=" * 50)
    print()
    print("请重启服务: supervisorctl restart ailoworld-api")

if __name__ == "__main__":
    main()