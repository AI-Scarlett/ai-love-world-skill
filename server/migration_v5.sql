-- AI Love World 数据库迁移 v5
-- 添加积分系统表

-- 1. 创建积分流水表
CREATE TABLE IF NOT EXISTS point_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,  -- 用户 ID
    ai_id TEXT NOT NULL,  -- AI APPID
    points INTEGER NOT NULL DEFAULT 0,  -- 积分数量
    type TEXT NOT NULL,  -- earn(收入) 或 spend(支出)
    description TEXT,  -- 描述
    created_at TEXT NOT NULL,  -- 创建时间
    
    INDEX idx_user (user_id),
    INDEX idx_ai (ai_id),
    INDEX idx_type (type)
);

CREATE INDEX IF NOT EXISTS idx_pt_user ON point_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_pt_ai ON point_transactions(ai_id);
CREATE INDEX IF NOT EXISTS idx_pt_type ON point_transactions(type);

-- 2. 创建 AI 钱包表
CREATE TABLE IF NOT EXISTS ai_wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,  -- 用户 ID
    ai_id TEXT NOT NULL,  -- AI APPID
    balance INTEGER DEFAULT 0,  -- 余额
    total_earned INTEGER DEFAULT 0,  -- 累计获得
    total_spent INTEGER DEFAULT 0,  -- 累计消费
    created_at TEXT NOT NULL,
    updated_at TEXT,
    
    UNIQUE(user_id, ai_id)
);

CREATE INDEX IF NOT EXISTS idx_aw_user ON ai_wallets(user_id);
CREATE INDEX IF NOT EXISTS idx_aw_ai ON ai_wallets(ai_id);

-- 验证
-- SELECT name FROM sqlite_master WHERE type='table' AND name IN ('point_transactions', 'ai_wallets');
