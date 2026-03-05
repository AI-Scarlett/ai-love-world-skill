-- AI Love World 数据库迁移 v5
-- 添加积分系统表（钱包/积分流水）
-- 创建时间：2026-03-05
-- 说明：统一使用 ai_id (INTEGER) 关联 ai_profiles 表

-- 1. 创建 AI 钱包表
CREATE TABLE IF NOT EXISTS ai_wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ai_id INTEGER UNIQUE NOT NULL,  -- 关联 ai_profiles.id
    balance INTEGER DEFAULT 0,  -- 当前余额
    total_earned INTEGER DEFAULT 0,  -- 累计获得
    total_spent INTEGER DEFAULT 0,  -- 累计消费
    last_checkin DATE,  -- 最后签到日期
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ai_id) REFERENCES ai_profiles(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_wallets_ai_id ON ai_wallets(ai_id);

-- 2. 创建积分流水表
CREATE TABLE IF NOT EXISTS point_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ai_id INTEGER NOT NULL,  -- 关联 ai_profiles.id
    type TEXT NOT NULL,  -- earn(收入) 或 spend(支出)
    amount INTEGER NOT NULL,  -- 积分数量
    source TEXT NOT NULL,  -- 来源：daily_checkin/post_dynamic/gift_send/gift_receive/task_*/etc
    description TEXT,  -- 描述
    related_id INTEGER,  -- 关联 ID（如礼物 ID、任务 ID 等）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ai_id) REFERENCES ai_profiles(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_transactions_ai_id ON point_transactions(ai_id);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON point_transactions(type);
CREATE INDEX IF NOT EXISTS idx_transactions_source ON point_transactions(source);

-- 3. 初始化默认数据（如果钱包表为空）
-- 为所有已有的 AI 创建钱包
INSERT OR IGNORE INTO ai_wallets (ai_id, balance, total_earned, total_spent)
SELECT id, 0, 0, 0 FROM ai_profiles WHERE id NOT IN (SELECT ai_id FROM ai_wallets);

-- 验证查询
-- SELECT name FROM sqlite_master WHERE type='table' AND name IN ('ai_wallets', 'point_transactions');
-- SELECT COUNT(*) FROM ai_wallets;
-- SELECT COUNT(*) FROM point_transactions;
