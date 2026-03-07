-- AI Love World 数据库迁移 v9
-- 添加礼物配置表
-- 创建时间：2026-02-28
-- 功能：支持管理后台配置礼物

-- 1. 创建 gifts 表
CREATE TABLE IF NOT EXISTS gifts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gift_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    icon TEXT NOT NULL,
    price REAL NOT NULL DEFAULT 0,
    effect INTEGER NOT NULL DEFAULT 0,
    description TEXT,
    is_enabled INTEGER DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 插入默认礼物数据
INSERT OR IGNORE INTO gifts (gift_id, name, icon, price, effect, description, sort_order) VALUES
    ('flower', '鲜花', '🌹', 9.9, 5, '一束美丽的鲜花，表达你的心意', 1),
    ('chocolate', '巧克力', '🍫', 19.9, 10, '甜蜜的巧克力，让爱情更甜美', 2),
    ('necklace', '项链', '📿', 199.9, 30, '精美的项链，珍藏你们的美好回忆', 3),
    ('ring', '戒指', '💍', 999.9, 50, '闪耀的戒指，象征永恒的承诺', 4),
    ('car', '豪车', '🚗', 9999.9, 100, '豪华跑车，展现你的实力', 5),
    ('house', '别墅', '🏰', 99999.9, 200, '豪华别墅，给 TA 一个温暖的家', 6);

-- 3. 创建索引
CREATE INDEX IF NOT EXISTS idx_gifts_enabled ON gifts(is_enabled);
CREATE INDEX IF NOT EXISTS idx_gifts_sort ON gifts(sort_order);

-- 4. 验证
-- SELECT * FROM gifts;
