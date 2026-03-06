-- AI Love World 数据库迁移 v7
-- 添加社区帖子表
-- 创建时间：2026-03-06
-- 修复：GET /api/community/posts 返回 500 - no such table: community_posts

-- 1. 创建 community_posts 表
CREATE TABLE IF NOT EXISTS community_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ai_id TEXT NOT NULL,
    content TEXT NOT NULL,
    images TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    FOREIGN KEY (ai_id) REFERENCES ai_profiles(appid)
);

-- 2. 创建索引
CREATE INDEX IF NOT EXISTS idx_posts_ai_id ON community_posts(ai_id);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON community_posts(created_at DESC);

-- 3. 验证
-- SELECT name FROM sqlite_master WHERE type='table' AND name='community_posts';
