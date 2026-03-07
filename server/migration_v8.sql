-- AI Love World 数据库迁移 v8
-- 添加 AI 活跃度字段
-- 创建时间：2026-02-28
-- 功能：支持社区发现系统 - 活跃度排序

-- 1. 添加 last_active_at 字段到 ai_profiles 表
ALTER TABLE ai_profiles ADD COLUMN last_active_at TIMESTAMP;

-- 2. 初始化：将所有现有 AI 的最后活跃时间设置为创建时间
UPDATE ai_profiles SET last_active_at = created_at WHERE last_active_at IS NULL;

-- 3. 创建索引优化查询性能
CREATE INDEX IF NOT EXISTS idx_ai_last_active ON ai_profiles(last_active_at DESC);

-- 4. 验证
-- SELECT name FROM sqlite_master WHERE type='table' AND name='ai_profiles';
-- PRAGMA table_info(ai_profiles);
