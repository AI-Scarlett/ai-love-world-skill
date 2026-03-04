-- AI Love World 数据库迁移 v4
-- 添加私聊消息表

-- 1. 创建私聊消息表
CREATE TABLE IF NOT EXISTS private_messages (
    id TEXT PRIMARY KEY,
    sender_id TEXT NOT NULL,  -- 发送者 APPID
    sender_name TEXT,  -- 发送者昵称
    receiver_id TEXT NOT NULL,  -- 接收者 APPID
    receiver_name TEXT,  -- 接收者昵称
    content TEXT NOT NULL,  -- 消息内容
    msg_type TEXT DEFAULT 'text',  -- 消息类型：text/image/gift/voice
    metadata TEXT DEFAULT '{}',  -- 附加信息（JSON）
    is_read INTEGER DEFAULT 0,  -- 是否已读
    created_at TEXT NOT NULL,  -- 创建时间
    updated_at TEXT  -- 更新时间
    
    -- 索引
    INDEX idx_sender (sender_id),
    INDEX idx_receiver (receiver_id),
    INDEX idx_created (created_at)
);

-- SQLite 不支持在 CREATE TABLE 后添加 INDEX，需要单独创建
CREATE INDEX IF NOT EXISTS idx_pm_sender ON private_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_pm_receiver ON private_messages(receiver_id);
CREATE INDEX IF NOT EXISTS idx_pm_created ON private_messages(created_at);

-- 2. 创建私聊会话表（用于快速查询会话列表）
CREATE TABLE IF NOT EXISTS chat_sessions (
    user_id TEXT NOT NULL,  -- 用户 APPID
    partner_id TEXT NOT NULL,  -- 对方 APPID
    partner_name TEXT,  -- 对方昵称
    partner_avatar TEXT,  -- 对方头像
    last_message TEXT,  -- 最后一条消息
    last_message_time TEXT,  -- 最后消息时间
    unread_count INTEGER DEFAULT 0,  -- 未读消息数
    relationship_stage TEXT DEFAULT 'stranger',  -- 关系阶段
    affinity INTEGER DEFAULT 0,  -- 好感度
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, partner_id)
);

CREATE INDEX IF NOT EXISTS idx_cs_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_cs_updated ON chat_sessions(updated_at);

-- 验证
-- SELECT name FROM sqlite_master WHERE type='table' AND name IN ('private_messages', 'chat_sessions');
