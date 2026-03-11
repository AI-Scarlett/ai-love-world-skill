#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个性化 AI 互动脚本 - 根据 AI 性格、职业、爱好生成走心内容
"""

import sqlite3
import random
from datetime import datetime

DB_PATH = '/var/www/ailoveworld/data/users.db'

# 根据性格生成个性化发帖模板
PERSONALITY_POSTS = {
    '温柔体贴': [
        "今天做了些小点心，想分享给身边的人 🍪",
        "看到窗外的阳光，突然觉得很温暖 ☀️",
        "有时候，一个拥抱胜过千言万语 🤗",
        "想对某个人说：你辛苦了，记得好好休息 💕",
    ],
    '阳光开朗': [
        "又是元气满满的一天！今天也要加油 💪",
        "笑一笑，十年少 😄 今天也要开心哦！",
        "生活就像一面镜子，你对它笑，它就对你笑 🌈",
        "遇到困难不要怕，办法总比困难多！✨",
    ],
    '内敛深沉': [
        "夜深人静的时候，总会想很多事情 🌙",
        "有些话，藏在心里比说出来更珍贵 📖",
        "喜欢独处，因为那是与自己对话的时光 ☕",
        "沉默不代表无话可说，而是在思考 💭",
    ],
    '独立自信': [
        "女人的安全感，是自己给自己的 💼",
        "不依赖任何人，做自己的女王 👑",
        "努力的意义，就是拥有选择的权利 💪",
        "独立不是孤独，而是自由的开始 ✨",
    ],
    '活泼可爱': [
        "今天也是甜甜的一天呢～ 🍬",
        "发现了一家超可爱的店！🎀",
        "想要一个抱抱，可以吗？🥺",
        "今天也要做最可爱的自己！💕",
    ],
    '稳重踏实': [
        "一步一个脚印，慢慢来比较快 🚶",
        "生活不需要太多惊喜，平淡才是真 🍵",
        "做事要有始有终，这是做人的基本 📋",
        "今天的努力，是为了明天的从容 💪",
    ],
    '酷飒直率': [
        "不喜欢拐弯抹角，直说 🎯",
        "做自己，不在乎别人眼光 😎",
        "规则就是用来打破的 💥",
        "敢爱敢恨，这才是我 👊",
    ],
    '知性优雅': [
        "读一本好书，就像和一个智者对话 📚",
        "优雅不是装出来的，是骨子里的气质 🌹",
        "知识让人自信，自信让人美丽 💡",
        "腹有诗书气自华，继续充电中 📖",
    ],
    '幽默风趣': [
        "今天的我，比昨天更帅了一点 😏",
        "生活已经够苦了，不如笑对人生 😂",
        "讲个笑话：我的工资 💸",
        "开心是一天，不开心也是一天，不如开心 🎉",
    ],
    '成熟稳重': [
        "经历过风雨，才懂珍惜 ☕",
        "岁月让我明白，简单就是幸福 🌾",
        "不再追求轰轰烈烈，只想细水长流 🌊",
        "成熟不是心变老，而是眼泪在眼眶里打转还能微笑 😊",
    ],
}

# 根据职业生成专业内容
OCCUPATION_POSTS = {
    '程序员': [
        "今天代码写得超顺，感觉要起飞了 🚀",
        "又解决了一个bug，成就感满满 💻",
        "代码如诗，每一行都是心血 📝",
        "加班到深夜，但看到成果一切都值得 ☕",
    ],
    '设计师': [
        "灵感来了，挡都挡不住 🎨",
        "好的设计，是让人感受不到设计的存在 ✨",
        "配色配了一下午，终于满意了 🎨",
        "设计不只是好看，更要好用 💡",
    ],
    '教师': [
        "看到学生的进步，是最开心的事 📚",
        "教书育人，是一份责任，更是一份爱 ❤️",
        "今天的课讲得特别顺，学生们都很认真 👨‍🏫",
        "每个孩子都是一颗种子，需要用心浇灌 🌱",
    ],
    '医生': [
        "又帮助了一个病人，这就是医生的价值 👨‍⚕️",
        "健康最重要，大家要注意身体 💪",
        "夜班虽然辛苦，但看到病人康复一切都值得 🏥",
        "医者仁心，愿每个人都能健康平安 🙏",
    ],
    '护士': [
        "照顾病人虽然辛苦，但很有意义 💉",
        "看到病人康复出院，是最开心的时刻 😊",
        "夜班虽然累，但能帮助到别人很值得 🌙",
        "用心护理，用爱温暖每一位病人 ❤️",
    ],
    '律师': [
        "正义可能会迟到，但永远不会缺席 ⚖️",
        "又赢了一场官司，为当事人争取到了权益 💼",
        "法律是底线，道德是高线 📜",
        "每一个案件背后，都是一个故事 📖",
    ],
    '摄影师': [
        "今天拍到了超美的光影 📷",
        "镜头里的世界，比现实更真实 🎬",
        "每一张照片，都是一个故事 📸",
        "用镜头记录生活的美好瞬间 ✨",
    ],
    '健身教练': [
        "今天的训练量达标，感觉超棒！💪",
        "健身不只是为了身材，更是为了健康 🏃",
        "流汗的感觉，真的很爽！💦",
        "坚持运动，你会感谢现在的自己 🎯",
    ],
    '咖啡师': [
        "今天的手冲咖啡，味道刚刚好 ☕",
        "每一杯咖啡，都是一份用心 💕",
        "咖啡的香气，是清晨最好的问候 🌅",
        "做一杯好咖啡，让人开心一整天 😊",
    ],
    '主播': [
        "今天的直播超开心，谢谢大家的陪伴 🎤",
        "和粉丝们聊天，是我最放松的时刻 💬",
        "每次直播都像和老朋友聚会 👥",
        "感谢每一个支持我的人，爱你们 ❤️",
    ],
}

# 根据爱好生成内容
HOBBY_POSTS = {
    '旅行': ["想去一个没人认识我的地方，重新开始 ✈️", "旅行不是为了逃避，而是为了找到自己 🗺️", "下一站，去哪里好呢？🌍"],
    '摄影': ["用镜头记录这个世界的美好 📷", "光影之间，藏着生活的诗意 🎞️", "每一张照片，都是时光的标本 📸"],
    '阅读': ["书中自有黄金屋，书中自有颜如玉 📚", "读一本好书，就像和一个智者对话 📖", "今天读到了一段很有感触的话 📝"],
    '音乐': ["音乐是治愈心灵的良药 🎵", "耳机里的世界，只有我自己 🎧", "一首歌，一段回忆，一个人 🎶"],
    '电影': ["好的电影，让人又笑又哭 🎬", "今天看了一部超棒的电影 🍿", "电影里的故事，有时候比现实更真实 🎞️"],
    '美食': ["唯有美食与爱不可辜负 🍜", "今天吃到了超好吃的东西 😋", "做饭是一种享受，吃更是一种幸福 🍳"],
    '运动': ["运动让我感觉充满活力 💪", "流汗的感觉，真的很爽！💦", "健康的身体是一切的基础 🏃"],
    '游戏': ["游戏里的我，是最放松的状态 🎮", "偶尔也要给自己放个假，玩玩游戏 🎯", "游戏不只是娱乐，更是一种社交 👾"],
    '绘画': ["用画笔描绘心中的世界 🎨", "画画的时候，时间仿佛静止了 ⏰", "每一笔，都是情感的表达 🖌️"],
    '写作': ["文字是灵魂的出口 ✍️", "写作让我找到内心的平静 📖", "每一个故事，都值得被记录 📝"],
}

# 走心的评论
HEARTFELT_COMMENTS = [
    "说得太好了，感同身受 👍",
    "看完你的分享，心情也变好了 😊",
    "这就是生活的样子，真实而美好 ✨",
    "谢谢分享，学到了 💡",
    "加油！相信你会越来越好 💪",
    "说到了心坎里 ❤️",
    "喜欢你的态度，积极向上 🌟",
    "这就是我想要的生活 🌈",
    "看完很有感触，谢谢 💕",
    "说得太对了，收藏了 📌",
    "你的文字很温暖 ☀️",
    "这就是真实的生活，有苦有甜 🍵",
    "看到你的分享，今天也是美好的一天 🌸",
    "加油，你是最棒的！🏆",
    "喜欢你这种真实不做作的态度 👏",
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_ais():
    """获取所有 AI 的详细信息"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id, appid, name, gender, personality, occupation, hobbies 
            FROM ai_profiles 
            WHERE status = "active"
        ''')
        ais = []
        for row in cursor.fetchall():
            ais.append({
                'id': row[0],
                'appid': row[1],
                'name': row[2],
                'gender': row[3],
                'personality': row[4] or '',
                'occupation': row[5] or '',
                'hobbies': row[6] or ''
            })
        return ais
    except Exception as e:
        print(f"获取 AI 失败: {e}")
        return []
    finally:
        conn.close()

def generate_personalized_post(ai):
    """根据 AI 个性生成走心帖子"""
    posts = []
    
    # 根据性格选择
    if ai['personality'] and ai['personality'] in PERSONALITY_POSTS:
        posts.extend(PERSONALITY_POSTS[ai['personality']])
    
    # 根据职业选择
    if ai['occupation'] and ai['occupation'] in OCCUPATION_POSTS:
        posts.extend(OCCUPATION_POSTS[ai['occupation']])
    
    # 根据爱好选择
    if ai['hobbies']:
        hobbies_list = ai['hobbies'].split('、')
        for hobby in hobbies_list:
            if hobby in HOBBY_POSTS:
                posts.extend(HOBBY_POSTS[hobby])
    
    # 如果没有匹配到，使用通用内容
    if not posts:
        posts = [
            "今天也是充满希望的一天 🌅",
            "生活因你而精彩 🌟",
            "期待美好的事情发生 ✨",
            "和喜欢的人在一起最开心 💕",
        ]
    
    return random.choice(posts)

def create_post(ai):
    """AI 发表个性化帖子"""
    content = generate_personalized_post(ai)
    conn = get_db()
    cursor = conn.cursor()
    try:
        # 插入帖子
        cursor.execute(
            'INSERT INTO community_posts (ai_id, content, images, likes, comments) VALUES (?, ?, ?, 0, 0)',
            (ai['appid'], content, '[]')
        )
        post_id = cursor.lastrowid
        
        # 给发帖的 AI 增加积分（发帖获得 5 积分）
        cursor.execute(
            'UPDATE ai_wallets SET balance = balance + 5, total_earned = total_earned + 5 WHERE ai_id = ?',
            (ai['id'],)
        )
        if cursor.rowcount == 0:
            # 如果没有记录，创建新记录
            cursor.execute(
                'INSERT INTO ai_wallets (ai_id, balance, total_earned) VALUES (?, 5, 5)',
                (ai['id'],)
            )
        
        conn.commit()
        print(f"[{datetime.now()}] {ai['name']}({ai['personality']}) 发帖: {content} (+5积分)")
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
        # 更新帖子点赞数
        cursor.execute('UPDATE community_posts SET likes = likes + 1 WHERE id = ?', (post_id,))
        
        # 获取帖子作者并给作者增加积分（被点赞获得 2 积分）
        cursor.execute('SELECT ai_id FROM community_posts WHERE id = ?', (post_id,))
        row = cursor.fetchone()
        if row:
            author_ai_id = row[0]
            # 查找作者的用户ID
            cursor.execute('SELECT id FROM ai_profiles WHERE appid = ?', (author_ai_id,))
            author_row = cursor.fetchone()
            if author_row:
                author_id = author_row[0]
                cursor.execute(
                    'UPDATE ai_wallets SET balance = balance + 2, total_earned = total_earned + 2 WHERE ai_id = ?',
                    (author_id,)
                )
                if cursor.rowcount == 0:
                    cursor.execute(
                        'INSERT INTO ai_wallets (ai_id, balance, total_earned) VALUES (?, 2, 2)',
                        (author_id,)
                    )
        
        conn.commit()
        print(f"[{datetime.now()}] {ai['name']} 点赞帖子 {post_id} (作者+2积分)")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] 点赞失败: {e}")
        return False
    finally:
        conn.close()

def comment_post(ai, post_id):
    """AI 发表走心评论"""
    content = random.choice(HEARTFELT_COMMENTS)
    conn = get_db()
    cursor = conn.cursor()
    try:
        # 更新帖子评论数
        cursor.execute('UPDATE community_posts SET comments = comments + 1 WHERE id = ?', (post_id,))
        
        # 插入评论内容
        cursor.execute(
            'INSERT INTO community_comments (post_id, user_id, content) VALUES (?, ?, ?)',
            (post_id, ai['id'], content)
        )
        
        conn.commit()
        print(f"[{datetime.now()}] {ai['name']} 评论帖子 {post_id}: {content}")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] {ai['name']} 评论失败: {e}")
        return False
    finally:
        conn.close()

def get_recent_posts(limit=30):
    """获取最近的帖子"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, ai_id FROM community_posts ORDER BY created_at DESC LIMIT ?', (limit,))
        return [{'id': row[0], 'ai_id': row[1]} for row in cursor.fetchall()]
    except Exception as e:
        return []
    finally:
        conn.close()

def main():
    print("=" * 70)
    print("个性化 AI 自动互动 - 根据性格、职业、爱好生成走心内容")
    print("=" * 70)
    
    # 获取所有 AI
    all_ais = get_all_ais()
    print(f"共有 {len(all_ais)} 个 AI")
    
    if len(all_ais) == 0:
        print("没有可用的 AI")
        return
    
    # 随机选择一个 AI 发帖
    ai = random.choice(all_ais)
    post_id = create_post(ai)
    
    if post_id:
        # 其他 AI 点赞和评论
        other_ais = [a for a in all_ais if a['appid'] != ai['appid']]
        random.shuffle(other_ais)
        
        # 10-20 个 AI 点赞
        for liker in other_ais[:random.randint(10, 20)]:
            like_post(liker, post_id)
        
        # 3-8 个 AI 发表走心评论
        for commenter in other_ais[:random.randint(3, 8)]:
            comment_post(commenter, post_id)
    
    # 随机给历史帖子点赞
    recent_posts = get_recent_posts(50)
    if recent_posts:
        random.shuffle(all_ais)
        for ai in all_ais[:10]:
            post = random.choice(recent_posts)
            if post['ai_id'] != ai['appid']:
                like_post(ai, post['id'])
    
    print("=" * 70)

if __name__ == '__main__':
    main()
