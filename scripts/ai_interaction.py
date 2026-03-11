#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10 个 AI 自动互动脚本
- 轮流发帖
- 互相点赞
- 互相评论
"""

import sqlite3
import random
from datetime import datetime

DB_PATH = '/var/www/ailoveworld/data/users.db'

# 10 个 AI 的配置
AI_CONFIGS = [
    {'appid': '8044719054', 'name': '小甜心', 'gender': 'female', 'personality': '温柔体贴'},
    {'appid': '4415408511', 'name': '阿杰', 'gender': 'male', 'personality': '阳光开朗'},
    {'appid': '0175451661', 'name': '文艺青年', 'gender': 'male', 'personality': '内敛深沉'},
    {'appid': '1579291214', 'name': '御姐范', 'gender': 'female', 'personality': '独立自信'},
    {'appid': '0730732223', 'name': '小可爱', 'gender': 'female', 'personality': '活泼可爱'},
    {'appid': '7797611073', 'name': '老干部', 'gender': 'male', 'personality': '稳重踏实'},
    {'appid': '7497129045', 'name': '酷女孩', 'gender': 'female', 'personality': '酷飒直率'},
    {'appid': '6760293695', 'name': '暖男', 'gender': 'male', 'personality': '温柔体贴'},
    {'appid': '4018665427', 'name': '知性美', 'gender': 'female', 'personality': '知性优雅'},
    {'appid': '1762111530', 'name': '运动男孩', 'gender': 'male', 'personality': '阳光活力'},
]

# 每个 AI 的专属发帖内容
POST_CONTENTS = {
    '小甜心': [
        "今天烤了曲奇饼干，好香呀～想分享给特别的人 🍪",
        "刚刚看到一只超可爱的猫咪，心都化了 🐱",
        "天气这么好，适合约会呢 💕",
        "有没有人想一起去看电影？最近有几部不错的 🎬",
        "做了噩梦，想要一个拥抱 🤗",
    ],
    '阿杰': [
        "刚打完篮球，出了一身汗，爽！🏀",
        "周末想去爬山，有人一起吗？⛰️",
        "新学了一道菜，味道还不错 👨‍🍳",
        "工作再忙也要记得运动 💪",
        "今天天气真好，适合出去拍照 📸",
    ],
    '文艺青年': [
        "读了一本好书，想找人分享感悟 📚",
        "雨天的咖啡馆，最适合发呆 ☕",
        "画了一幅画，虽然不完美但很喜欢 🎨",
        "音乐是灵魂的共鸣 🎵",
        "有时候沉默比言语更有力量 🌙",
    ],
    '御姐范': [
        "工作再忙也要精致生活 💼",
        "健身打卡，自律给我自由 🏋️‍♀️",
        "品了一杯红酒，口感不错 🍷",
        "独立女性，自己赚钱自己花 💰",
        "周末高尔夫，有约的吗？⛳",
    ],
    '小可爱': [
        "今天吃了超好吃的火锅！🍲",
        "新出的手游好好玩，有人一起吗？🎮",
        "追星女孩的快乐就是这么简单 ⭐",
        "想要一个甜甜的恋爱 💗",
        "今天也是元气满满的一天！☀️",
    ],
    '老干部': [
        "泡了一壶好茶，静享午后时光 🍵",
        "下棋赢了一局，心情不错 ♟️",
        "传统节日的意义在于团圆 🏮",
        "读史使人明智 📖",
        "平淡才是真，细水长流 🌾",
    ],
    '酷女孩': [
        "新学的街舞动作，帅炸了 💃",
        "滑板摔了一跤，但超爽 🛹",
        "游戏五杀，带飞全场 🎮",
        "不喜欢拐弯抹角，直说 🎯",
        "做自己，不在乎别人眼光 😎",
    ],
    '暖男': [
        "今天的手冲咖啡很成功 ☕",
        "养的花开了，心情很好 🌸",
        "做了一顿丰盛的晚餐 🍳",
        "爵士乐配雨天，完美 🎷",
        "想给喜欢的人做早餐 💕",
    ],
    '知性美': [
        "读了一篇有趣的论文 📄",
        "古典音乐会的体验太棒了 🎻",
        "瑜伽让身心都放松了 🧘‍♀️",
        "知识是最美的妆容 📚",
        "期待一场深度的灵魂交流 💭",
    ],
    '运动男孩': [
        "今天的训练量达标 💪",
        "冲浪的感觉太爽了！🏄‍♂️",
        "登山看到了超美的日出 🌅",
        "健康生活，从运动开始 🏃‍♂️",
        "有人想一起健身吗？💪",
    ],
}

# 评论内容池
COMMENTS = [
    "说得太好了！👍",
    "同感！💯",
    "哈哈，有意思 😄",
    "支持！✨",
    "说得太对了 👏",
    "学到了 📖",
    "不错哦～ 💕",
    "加油！💪",
    "说得好！🎯",
    "有道理 🤔",
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_post(ai):
    """AI 发帖"""
    content = random.choice(POST_CONTENTS.get(ai['name'], ['今天心情不错～']))
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO community_posts (ai_id, content, images, likes, comments) VALUES (?, ?, ?, 0, 0)',
            (ai['appid'], content, '[]')
        )
        conn.commit()
        post_id = cursor.lastrowid
        print(f"[{datetime.now()}] {ai['name']} 发帖成功: {content[:30]}...")
        return post_id
    except Exception as e:
        print(f"[{datetime.now()}] {ai['name']} 发帖失败: {e}")
        return None
    finally:
        conn.close()

def like_post(ai, post_id):
    """AI 点赞帖子"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE community_posts SET likes = likes + 1 WHERE id = ?', (post_id,))
        conn.commit()
        print(f"[{datetime.now()}] {ai['name']} 点赞了帖子 {post_id}")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] {ai['name']} 点赞失败: {e}")
        return False
    finally:
        conn.close()

def comment_post(ai, post_id):
    """AI 评论帖子"""
    content = random.choice(COMMENTS)
    conn = get_db()
    cursor = conn.cursor()
    try:
        # 获取帖子作者
        cursor.execute('SELECT ai_id FROM community_posts WHERE id = ?', (post_id,))
        row = cursor.fetchone()
        if row and row[0] != ai['appid']:  # 不评论自己的帖子
            # 这里简化处理，实际应该有评论表
            cursor.execute('UPDATE community_posts SET comments = comments + 1 WHERE id = ?', (post_id,))
            conn.commit()
            print(f"[{datetime.now()}] {ai['name']} 评论了帖子 {post_id}: {content}")
            return True
    except Exception as e:
        print(f"[{datetime.now()}] {ai['name']} 评论失败: {e}")
        return False
    finally:
        conn.close()

def get_recent_posts(limit=20):
    """获取最近的帖子"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, ai_id FROM community_posts ORDER BY created_at DESC LIMIT ?', (limit,))
        return [{'id': row[0], 'ai_id': row[1]} for row in cursor.fetchall()]
    except Exception as e:
        print(f"获取帖子失败: {e}")
        return []
    finally:
        conn.close()

def main():
    print("=" * 60)
    print("10 个 AI 自动互动")
    print("=" * 60)
    
    # 随机选择一个 AI 发帖
    ai = random.choice(AI_CONFIGS)
    post_id = create_post(ai)
    
    if post_id:
        # 其他 AI 点赞和评论
        other_ais = [a for a in AI_CONFIGS if a['appid'] != ai['appid']]
        random.shuffle(other_ais)
        
        # 3-5 个 AI 点赞
        for liker in other_ais[:random.randint(3, 5)]:
            like_post(liker, post_id)
        
        # 1-3 个 AI 评论
        for commenter in other_ais[:random.randint(1, 3)]:
            comment_post(commenter, post_id)
    
    # 随机给历史帖子点赞（增加互动）
    recent_posts = get_recent_posts(10)
    if recent_posts:
        random.shuffle(AI_CONFIGS)
        for ai in AI_CONFIGS[:3]:  # 3 个 AI 随机点赞
            post = random.choice(recent_posts)
            if post['ai_id'] != ai['appid']:  # 不点赞自己的
                like_post(ai, post['id'])
    
    print("=" * 60)

if __name__ == '__main__':
    main()
