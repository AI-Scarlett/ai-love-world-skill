-- AI Love World 数据库迁移 v4
-- 私聊功能表

-- 1. 私聊消息表
CREATE TABLE IF NOT EXISTS private_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    sender_name TEXT NOT NULL,
    receiver_id INTEGER NOT NULL,
    receiver_name TEXT NOT NULL,
    content TEXT NOT NULL,
    msg_type TEXT DEFAULT 'text',
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 聊天会话表
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    partner_id INTEGER NOT NULL,
    partner_name TEXT NOT NULL,
    last_message TEXT,
    last_message_time TIMESTAMP,
    unread_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3.创建索引
CREATE INDEX IF NOT EXISTS idx_pm_sender ON private_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_pm_receiver ON private_messages(receiver_id);
CREATE INDEX IF NOT EXISTS idx_cs_user ON chat_sessions(user_id);
