-- AI Love World 数据库迁移脚本
-- 从 birth_date 改为 age 字段

-- 1. 检查表是否存在
-- 如果 ai_profiles 表有 birth_date 字段，需要迁移

-- 2. 添加 age 字段（如果不存在）
ALTER TABLE ai_profiles ADD COLUMN age INTEGER DEFAULT 18;

-- 3. 从 birth_date 计算 age 并更新（如果有的话）
-- UPDATE ai_profiles SET age = (strftime('%Y', 'now') - strftime('%Y', birth_date)) WHERE birth_date IS NOT NULL;

-- 4. 删除 birth_date 字段（SQLite 不支持直接删除，需要重建表）
-- 如果需要完全清理，请使用下面的重建方法：

/*
-- 备份数据
CREATE TABLE ai_profiles_backup AS SELECT * FROM ai_profiles;

-- 删除旧表
DROP TABLE ai_profiles;

-- 创建新表（不含 birth_date）
CREATE TABLE ai_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    appid TEXT UNIQUE NOT NULL,
    api_key TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    gender TEXT NOT NULL,
    age INTEGER DEFAULT 18,
    nationality TEXT DEFAULT 'CN',
    city TEXT DEFAULT '',
    education TEXT DEFAULT '',
    height INTEGER,
    personality TEXT DEFAULT '',
    occupation TEXT DEFAULT '',
    hobbies TEXT DEFAULT '',
    appearance TEXT DEFAULT '',
    background TEXT DEFAULT '',
    love_preference TEXT DEFAULT '',
    sexual_orientation TEXT DEFAULT 'heterosexual',
    avatar_id INTEGER,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 恢复数据
INSERT INTO ai_profiles 
SELECT id, user_id, appid, api_key, name, gender, age, nationality, city, education, height, 
       personality, occupation, hobbies, appearance, background, love_preference, 
       sexual_orientation, avatar_id, status, created_at, updated_at
FROM ai_profiles_backup;

-- 删除备份
DROP TABLE ai_profiles_backup;
*/

-- 简单方式：直接添加 age 字段
-- ALTER TABLE ai_profiles ADD COLUMN age INTEGER DEFAULT 18;