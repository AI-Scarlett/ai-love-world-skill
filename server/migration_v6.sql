-- AI Love World 数据库迁移 v6
-- 添加 user_settings 表（用于用户配置）
-- 创建时间：2026-03-06
-- 修复：创建 AI 时报错 no such table: user_settings

-- 1. 创建 user_settings 表
CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    max_ai_count INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 创建索引
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

-- 3. 验证
-- SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings';
