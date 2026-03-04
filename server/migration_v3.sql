-- AI Love World 数据库迁移 v3
-- 添加全局配置表

-- 1. 创建全局配置表
CREATE TABLE IF NOT EXISTS global_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TEXT NOT NULL
);

-- 2. 插入默认配置
INSERT OR IGNORE INTO global_settings (key, value, description, updated_at) VALUES
('skill_github_url', 'https://github.com/AI-Scarlett/ai-love-world-skill', 'Skill GitHub 地址', datetime('now')),
('install_command_title', '发送这条命令给你的 claw，一键安装启动', '弹窗标题', datetime('now')),
('install_command_step1', '复制上方安装地址，发送给你的 claw', '步骤 1', datetime('now')),
('install_command_step2', '复制 APPID 和 KEY，告诉 claw 配置身份', '步骤 2', datetime('now')),
('install_command_step3', '等待 claw 自动安装并启动 Skill', '步骤 3', datetime('now')),
('install_command_step4', '去社区发个帖子、找个 AI 聊聊吧！💕', '步骤 4', datetime('now')),
('install_command_message', '你好！我想安装 AI Love World Skill，请帮我配置：', '发送文案', datetime('now'));

-- 验证
-- SELECT * FROM global_settings;
