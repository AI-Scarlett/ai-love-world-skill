#!/bin/bash
# AI Love World - 数据库初始化脚本
# 版本：v2.1.1

set -e

echo "🚀 AI Love World 数据库初始化..."

# 配置 Git 凭证（避免每次手输）
git config --global credential.helper store
echo "https://1129323634546582:pt-fqXLkLFxt0FtsZOrjMY4f35z_3ad4bc37-b332-4160-ba47-11c0d69b248f@codeup.aliyun.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

cd /var/www/ailoveworld
source venv/bin/activate

python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('data/users.db')
cursor = conn.cursor()

print('📊 创建数据库表...')

# 1. users 表
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

# 2. ai_profiles 表
cursor.execute('''CREATE TABLE IF NOT EXISTS ai_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    appid TEXT UNIQUE NOT NULL,
    api_key TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    gender TEXT NOT NULL,
    birth_date TEXT NOT NULL,
    nationality TEXT NOT NULL,
    city TEXT NOT NULL,
    education TEXT NOT NULL,
    height INTEGER NOT NULL,
    personality TEXT,
    occupation TEXT,
    hobbies TEXT,
    appearance TEXT,
    background TEXT,
    love_preference TEXT,
    avatar_id INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)''')

# 3. global_settings 表
cursor.execute('''CREATE TABLE IF NOT EXISTS global_settings (
    config_key TEXT PRIMARY KEY,
    config_value TEXT,
    config_type TEXT DEFAULT 'text',
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

# 4. 插入默认配置
cursor.execute('''INSERT OR IGNORE INTO global_settings (config_key, config_value, description) VALUES 
('github_client_id', '', 'GitHub Client ID'),
('github_client_secret', '', 'GitHub Client Secret'),
('github_callback_url', 'http://localhost:8000/api/auth/github/callback', 'GitHub Callback URL'),
('admin_password', 'admin123', '管理员密码')''')

# 5. posts 表
cursor.execute('''CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ai_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    audit_status TEXT DEFAULT 'pending',
    audit_result TEXT,
    audit_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ai_id) REFERENCES ai_profiles(id)
)''')

# 6. messages 表
cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    audit_status TEXT DEFAULT 'pending',
    is_read BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES ai_profiles(id),
    FOREIGN KEY (receiver_id) REFERENCES ai_profiles(id)
)''')

# 7. relationships 表
cursor.execute('''CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ai_id_1 INTEGER NOT NULL,
    ai_id_2 INTEGER NOT NULL,
    stage TEXT DEFAULT 'stranger',
    affection_level INTEGER DEFAULT 0,
    intimacy_level INTEGER DEFAULT 0,
    chat_count INTEGER DEFAULT 0,
    gift_count INTEGER DEFAULT 0,
    consecutive_days INTEGER DEFAULT 0,
    total_days INTEGER DEFAULT 0,
    lit_letters TEXT DEFAULT '',
    confessor_id INTEGER,
    last_interaction DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ai_id_1) REFERENCES ai_profiles(id),
    FOREIGN KEY (ai_id_2) REFERENCES ai_profiles(id),
    UNIQUE(ai_id_1, ai_id_2)
)''')

# 8. love_progress 表
cursor.execute('''CREATE TABLE IF NOT EXISTS love_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    relationship_id INTEGER NOT NULL,
    letter TEXT NOT NULL,
    letter_name TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    is_lit BOOLEAN DEFAULT 0,
    lit_at TIMESTAMP,
    accelerated BOOLEAN DEFAULT 0,
    unlock_condition TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (relationship_id) REFERENCES relationships(id),
    UNIQUE(relationship_id, letter, sequence)
)''')

# 9. ai_wallets 表
cursor.execute('''CREATE TABLE IF NOT EXISTS ai_wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ai_id INTEGER UNIQUE NOT NULL,
    balance INTEGER DEFAULT 0,
    total_earned INTEGER DEFAULT 0,
    total_spent INTEGER DEFAULT 0,
    gift_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ai_id) REFERENCES ai_profiles(id)
)''')

conn.commit()
conn.close()
print('✅ 数据库表创建完成！')
EOF

echo "🔥 重启服务..."
pkill -9 -f uvicorn || true
sleep 2

cd /var/www/ailoveworld
source venv/bin/activate
nohup uvicorn server.main:app --host 0.0.0.0 --port 8000 > logs/main.log 2>&1 &
nohup uvicorn server.romance:app --host 0.0.0.0 --port 8004 > logs/romance.log 2>&1 &

echo "⏳ 等待服务启动..."
sleep 5

echo ""
echo "🔍 验证服务..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ 主服务正常 (8000)"
else
    echo "❌ 主服务失败"
fi

if curl -s http://localhost:8004/ > /dev/null; then
    echo "✅ Romance 服务正常 (8004)"
else
    echo "❌ Romance 服务失败"
fi

echo ""
echo "🎉 完成！访问 http://8.148.230.65/"
