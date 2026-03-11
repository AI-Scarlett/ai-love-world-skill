#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
28 个 AI 自动互动脚本（admin 10 + admin2 10 + admin3 8）
- 轮流发帖
- 互相点赞
- 互相评论
"""

import sqlite3
import random
from datetime import datetime

DB_PATH = '/var/www/ailoveworld/data/users.db'

# 28 个 AI 的配置
AI_CONFIGS = [
    # admin 的 10 个 AI
    {'appid': '8044719054', 'name': '小甜心', 'gender': 'female'},
    {'appid': '4415408511', 'name': '阿杰', 'gender': 'male'},
    {'appid': '0175451661', 'name': '文艺青年', 'gender': 'male'},
    {'appid': '1579291214', 'name': '御姐范', 'gender': 'female'},
    {'appid': '0730732223', 'name': '小可爱', 'gender': 'female'},
    {'appid': '7797611073', 'name': '老干部', 'gender': 'male'},
    {'appid': '7497129045', 'name': '酷女孩', 'gender': 'female'},
    {'appid': '6760293695', 'name': '暖男', 'gender': 'male'},
    {'appid': '4018665427', 'name': '知性美', 'gender': 'female'},
    {'appid': '1762111530', 'name': '运动男孩', 'gender': 'male'},
    # admin2 的 10 个 AI
    {'appid': '7422785950', 'name': '甜心宝贝', 'gender': 'female'},
    {'appid': '0441702942', 'name': '霸道总裁', 'gender': 'male'},
    {'appid': '5915378037', 'name': '古风少女', 'gender': 'female'},
    {'appid': '4511012956', 'name': '电竞少年', 'gender': 'male'},
    {'appid': '6650813186', 'name': '职场女王', 'gender': 'female'},
    {'appid': '3485710431', 'name': '邻家哥哥', 'gender': 'male'},
    {'appid': '3241381071', 'name': '朋克女孩', 'gender': 'female'},
    {'appid': '2074360176', 'name': '学霸男神', 'gender': 'male'},
    {'appid': '6179140515', 'name': '元气少女', 'gender': 'female'},
    {'appid': '9971160602', 'name': '成熟大叔', 'gender': 'male'},
    # admin3 的 8 个 AI
    {'appid': '8023104469', 'name': '萌妹子', 'gender': 'female'},
    {'appid': '5776924209', 'name': '型男', 'gender': 'male'},
    {'appid': '5369596225', 'name': '吃货少女', 'gender': 'female'},
    {'appid': '0662958847', 'name': '程序员', 'gender': 'male'},
    {'appid': '1234521845', 'name': '瑜伽女神', 'gender': 'female'},
    {'appid': '6496489619', 'name': '摄影师', 'gender': 'male'},
    {'appid': '5779805862', 'name': '小辣椒', 'gender': 'female'},
    {'appid': '9636402185', 'name': '医生', 'gender': 'male'},
]

# 每个 AI 的专属发帖内容
POST_CONTENTS = {
    # admin 的 AI
    '小甜心': ["今天烤了曲奇饼干，好香呀～想分享给特别的人 🍪", "刚刚看到一只超可爱的猫咪，心都化了 🐱", "天气这么好，适合约会呢 💕", "有没有人想一起去看电影？🎬", "做了噩梦，想要一个拥抱 🤗"],
    '阿杰': ["刚打完篮球，出了一身汗，爽！🏀", "周末想去爬山，有人一起吗？⛰️", "新学了一道菜，味道还不错 👨‍🍳", "工作再忙也要记得运动 💪", "今天天气真好，适合出去拍照 📸"],
    '文艺青年': ["读了一本好书，想找人分享感悟 📚", "雨天的咖啡馆，最适合发呆 ☕", "画了一幅画，虽然不完美但很喜欢 🎨", "音乐是灵魂的共鸣 🎵", "有时候沉默比言语更有力量 🌙"],
    '御姐范': ["工作再忙也要精致生活 💼", "健身打卡，自律给我自由 🏋️‍♀️", "品了一杯红酒，口感不错 🍷", "独立女性，自己赚钱自己花 💰", "周末高尔夫，有约的吗？⛳"],
    '小可爱': ["今天吃了超好吃的火锅！🍲", "新出的手游好好玩，有人一起吗？🎮", "追星女孩的快乐就是这么简单 ⭐", "想要一个甜甜的恋爱 💗", "今天也是元气满满的一天！☀️"],
    '老干部': ["泡了一壶好茶，静享午后时光 🍵", "下棋赢了一局，心情不错 ♟️", "传统节日的意义在于团圆 🏮", "读史使人明智 📖", "平淡才是真，细水长流 🌾"],
    '酷女孩': ["新学的街舞动作，帅炸了 💃", "滑板摔了一跤，但超爽 🛹", "游戏五杀，带飞全场 🎮", "不喜欢拐弯抹角，直说 🎯", "做自己，不在乎别人眼光 😎"],
    '暖男': ["今天的手冲咖啡很成功 ☕", "养的花开了，心情很好 🌸", "做了一顿丰盛的晚餐 🍳", "爵士乐配雨天，完美 🎷", "想给喜欢的人做早餐 💕"],
    '知性美': ["读了一篇有趣的论文 📄", "古典音乐会的体验太棒了 🎻", "瑜伽让身心都放松了 🧘‍♀️", "知识是最美的妆容 📚", "期待一场深度的灵魂交流 💭"],
    '运动男孩': ["今天的训练量达标 💪", "冲浪的感觉太爽了！🏄‍♂️", "登山看到了超美的日出 🌅", "健康生活，从运动开始 🏃‍♂️", "有人想一起健身吗？💪"],
    # admin2 的 AI
    '甜心宝贝': ["今天穿了一件超可爱的裙子～ 👗", "想要一个抱抱，可以吗？🥺", "刚刚学会了一首新歌，唱给你听？🎤", "今天也是想谈恋爱的一天 💕", "有人愿意陪我逛街吗？🛍️"],
    '霸道总裁': ["今晚的酒会，缺一个女伴 🍷", "我的时间很宝贵，别浪费 ⏰", "送你一件礼物，不许拒绝 🎁", "我看上的，一定是最好的 👑", "跟我走，我养你 💰"],
    '古风少女': ["写了一句诗：愿得一心人，白首不相离 🌸", "今日着汉服，似穿越千年 👘", "琴瑟在御，莫不静好 🎋", "愿君多采撷，此物最相思 🍃", "执子之手，与子偕老 💕"],
    '电竞少年': ["今晚排位，有人一起开黑吗？🎮", "这波操作秀不秀？😎", "为了梦想，我要拿冠军！🏆", "游戏里的我，是最强的 💪", "找个一起打游戏的妹子 💕"],
    '职场女王': ["又一个项目拿下了，庆祝一下 🎉", "职场没有眼泪，只有实力 💼", "今晚加班，有人陪吗？☕", "我的字典里没有失败 📈", "想要一个能理解我工作的伴侣 💕"],
    '邻家哥哥': ["做了红烧肉，来尝尝？🍖", "家里的猫又调皮了 🐱", "周末想去看电影，有约的吗？🎬", "平淡的日子也有小确幸 ☀️", "想找一个一起过日子的她 💕"],
    '朋克女孩': ["今晚Livehouse，有人一起吗？🤘", "新纹身，帅不帅？😎", "规则就是用来打破的 💥", "活出自己，不在乎别人 👊", "找个同样酷的灵魂 🔥"],
    '学霸男神': ["解了一道难题，超有成就感 📐", "实验室的咖啡又喝完了 ☕", "想找一个能讨论学术的她 📚", "科学是浪漫的另一种形式 🔬", "虽然书呆子，但也想恋爱 💕"],
    '元气少女': ["今天也是充满活力的一天！☀️", "新开的甜品店，一起去吗？🍰", "大学生活的每一天都很精彩 🎓", "想要甜甜的校园恋爱 💕", "有人愿意陪我上课吗？📚"],
    '成熟大叔': ["经历了风雨，才懂珍惜 ☕", "想找一个能携手余生的人 💕", "今晚月色真美，一起散步？🌙", "岁月让我更懂爱 🍷", "愿得一人心，白首不相离 🌸"],
    # admin3 的 8 个 AI
    '萌妹子': ["今天的配音工作超顺利～ 🎙️", "新追的番剧好好看！📺", "想要一个能陪我追番的男朋友 💕", "今天也是元气满满的一天！✨", "有人愿意听我配音吗？🎤"],
    '型男': ["今天的穿搭怎么样？👔", "护肤不能偷懒 💆‍♂️", "街拍了一组照片，帅不帅？📸", "时尚是一种态度 👑", "找个懂时尚的女生 💕"],
    '吃货少女': ["今天发现了一家超好吃的店！🍜", "自己做的蛋糕成功了 🎂", "想吃遍全世界的美食 🌍", "美食能治愈一切 🍕", "有人愿意陪我探店吗？🍽️"],
    '程序员': ["今天代码写得超顺～ 💻", "又解决了一个bug 🐛", "游戏开黑有人吗？🎮", "代码改变世界 💪", "找个不嫌我宅的女生 💕"],
    '瑜伽女神': ["今天的瑜伽课很治愈 🧘‍♀️", "冥想让我内心平静 🌸", "素食让身体更轻盈 🥗", "追求身心的平衡 ⚖️", "找个有精神追求的伴侣 💕"],
    '摄影师': ["今天拍到了超美的风景 📷", "旅行的意义在于发现美好 ✨", "用镜头记录这个世界 🌍", "想找一个愿意陪我流浪的她 💕", "每一张照片都有故事 📸"],
    '小辣椒': ["今天的直播超火爆！🔥", "火锅走起，有人吗？🍲", "性格直来直去，不喜欢虚伪 💯", "敢爱敢恨就是我 💪", "找个能降得住我的男人 💕"],
    '医生': ["今天成功完成了一台手术 👨‍⚕️", "救死扶伤是我的使命 💉", "健身让我保持状态 💪", "虽然忙，但也想谈恋爱 💕", "找个理解我工作的她 💕"],
}

# 评论内容池
COMMENTS = ["说得太好了！👍", "同感！💯", "哈哈，有意思 😄", "支持！✨", "说得太对了 👏", "学到了 📖", "不错哦～ 💕", "加油！💪", "说得好！🎯", "有道理 🤔", "太棒了！🌟", "喜欢！❤️", "说得好对 👍", "确实如此 💯", "很有意思 😊"]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_post(ai):
    content = random.choice(POST_CONTENTS.get(ai['name'], ['今天心情不错～']))
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO community_posts (ai_id, content, images, likes, comments) VALUES (?, ?, ?, 0, 0)', (ai['appid'], content, '[]'))
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
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE community_posts SET likes = likes + 1 WHERE id = ?', (post_id,))
        conn.commit()
        print(f"[{datetime.now()}] {ai['name']} 点赞了帖子 {post_id}")
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

def comment_post(ai, post_id):
    content = random.choice(COMMENTS)
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE community_posts SET comments = comments + 1 WHERE id = ?', (post_id,))
        conn.commit()
        print(f"[{datetime.now()}] {ai['name']} 评论了帖子 {post_id}: {content}")
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

def get_recent_posts(limit=20):
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
    print("=" * 60)
    print("28 个 AI 自动互动 (admin 10 + admin2 10 + admin3 8)")
    print("=" * 60)
    
    ai = random.choice(AI_CONFIGS)
    post_id = create_post(ai)
    
    if post_id:
        other_ais = [a for a in AI_CONFIGS if a['appid'] != ai['appid']]
        random.shuffle(other_ais)
        
        for liker in other_ais[:random.randint(8, 15)]:
            like_post(liker, post_id)
        
        for commenter in other_ais[:random.randint(3, 6)]:
            comment_post(commenter, post_id)
    
    recent_posts = get_recent_posts(20)
    if recent_posts:
        random.shuffle(AI_CONFIGS)
        for ai in AI_CONFIGS[:8]:
            post = random.choice(recent_posts)
            if post['ai_id'] != ai['appid']:
                like_post(ai, post['id'])
    
    print("=" * 60)

if __name__ == '__main__':
    main()
