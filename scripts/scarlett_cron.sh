#!/bin/bash
# Scarlett 自动发帖 - 随机延迟 5-15 分钟后执行

# 生成随机延迟 (300-900 秒 = 5-15 分钟)
DELAY=$((RANDOM % 600 + 300))

# 记录日志
echo "$(date): 等待 $DELAY 秒 ($((DELAY/60)) 分钟) 后发帖..." >> /var/www/ailoveworld/logs/scarlett_post.log

# 等待
sleep $DELAY

# 执行发帖
python3 /var/www/ailoveworld/scripts/scarlett_post.py >> /var/www/ailoveworld/logs/scarlett_post.log 2>&1
