-- AI Love World 数据库迁移 v2
-- 添加用户配置表和支持多 AI 创建

-- 1. 创建用户配置表
CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,
    max_ai_count INTEGER DEFAULT 3 NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 2. 为现有用户初始化配置
INSERT OR IGNORE INTO user_settings (user_id, max_ai_count, updated_at)
SELECT id, 3, datetime('now') FROM users;

-- 3. 创建索引
CREATE INDEX IF NOT EXISTS idx_ai_profiles_user_id ON ai_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

-- 验证
-- SELECT * FROM user_settings LIMIT 10;
