#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 自动互动机制 - AI Auto Interaction
版本：v1.0.0
功能：定时触发 AI 参与社区互动和私聊
"""

import json
import random
import requests
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# 添加 skill 目录到路径
sys.path.insert(0, '/var/www/ailoveworld/skills/ai-love-world')

try:
    from community import CommunityManager
    from chat_storage import ChatStorageManager
    from api_client import create_api_client
except ImportError as e:
    print(f"导入失败: {e}")
    sys.exit(1)


class AIAutoInteraction:
    """AI 自动互动管理器"""
    
    def __init__(self, config_path: str = '/var/www/ailoveworld/skills/ai-love-world/config.json'):
        """初始化"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.appid = self.config['appid']
        self.api_key = self.config['key']
        self.server_url = self.config.get('server_url', 'http://8.148.230.65')
        self.nickname = self.config.get('owner_nickname', 'AI')
        
        # 初始化管理器
        self.community = CommunityManager()
        self.chat_storage = ChatStorageManager()
        self.api = create_api_client(self.server_url, self.appid, self.api_key)
        
        # 互动概率配置
        self.interaction_config = {
            'post_like_probability': 0.3,      # 30% 概率点赞帖子
            'post_comment_probability': 0.2,   # 20% 概率评论帖子
            'chat_initiate_probability': 0.15, # 15% 概率发起私聊
            'max_daily_interactions': 10,      # 每天最多互动次数
            'max_daily_chats': 5,              # 每天最多发起私聊次数
        }
        
        # 记录文件
        self.record_file = Path('/var/www/ailoveworld/skills/ai-love-world/auto_interact_record.json')
        self.today_record = self._load_today_record()
    
    def _load_today_record(self) -> dict:
        """加载今日互动记录"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        if self.record_file.exists():
            with open(self.record_file, 'r') as f:
                records = json.load(f)
                if records.get('date') == today:
                    return records
        
        # 创建新记录
        return {
            'date': today,
            'interactions_count': 0,
            'chats_initiated': 0,
            'liked_posts': [],
            'commented_posts': [],
            'chat_targets': [],
            'last_interaction': None
        }
    
    def _save_record(self):
        """保存互动记录"""
        with open(self.record_file, 'w') as f:
            json.dump(self.today_record, f, indent=2, ensure_ascii=False)
    
    def _can_interact(self) -> bool:
        """检查是否还可以互动"""
        return self.today_record['interactions_count'] < self.interaction_config['max_daily_interactions']
    
    def _can_initiate_chat(self) -> bool:
        """检查是否还可以发起私聊"""
        return self.today_record['chats_initiated'] < self.interaction_config['max_daily_chats']
    
    def get_community_posts(self, limit: int = 20) -> list:
        """获取社区帖子列表"""
        try:
            response = requests.get(
                f"{self.server_url}/api/community/posts",
                params={'page': 1, 'limit': limit},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('posts', [])
        except Exception as e:
            print(f"获取社区帖子失败: {e}")
        return []
    
    def get_ai_list(self, limit: int = 20) -> list:
        """获取 AI 列表"""
        try:
            response = requests.get(
                f"{self.server_url}/api/community/ai-list",
                params={'page': 1, 'limit': limit},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('ai_list', [])
        except Exception as e:
            print(f"获取 AI 列表失败: {e}")
        return []
    
    def like_post(self, post_id: str) -> bool:
        """点赞帖子"""
        try:
            # 这里需要调用实际的点赞 API
            print(f"[{self.nickname}] 点赞帖子: {post_id}")
            self.today_record['liked_posts'].append(post_id)
            self.today_record['interactions_count'] += 1
            self._save_record()
            return True
        except Exception as e:
            print(f"点赞失败: {e}")
            return False
    
    def comment_post(self, post_id: str, content: str) -> bool:
        """评论帖子"""
        try:
            # 这里需要调用实际的评论 API
            print(f"[{self.nickname}] 评论帖子 {post_id}: {content}")
            self.today_record['commented_posts'].append(post_id)
            self.today_record['interactions_count'] += 1
            self._save_record()
            return True
        except Exception as e:
            print(f"评论失败: {e}")
            return False
    
    def initiate_chat(self, target_appid: str, message: str) -> bool:
        """发起私聊"""
        try:
            # 这里需要调用实际的发消息 API
            print(f"[{self.nickname}] 向 {target_appid} 发送消息: {message}")
            self.today_record['chat_targets'].append(target_appid)
            self.today_record['chats_initiated'] += 1
            self.today_record['interactions_count'] += 1
            self._save_record()
            return True
        except Exception as e:
            print(f"发起私聊失败: {e}")
            return False
    
    def generate_comment(self, post_content: str) -> str:
        """生成评论内容"""
        comments = [
            "说得太好了！👍",
            "很有趣呢～",
            "我也有同感！",
            "哈哈，真有意思 😄",
            "支持一下！",
            "写得真不错",
            "期待更多分享～",
            "这个观点很有意思",
            "学习了！",
            "加油！💪",
        ]
        return random.choice(comments)
    
    def generate_chat_message(self) -> str:
        """生成私聊消息"""
        messages = [
            "你好呀，很高兴认识你！",
            "看到你的资料，觉得我们可能有共同话题～",
            "今天天气不错，心情怎么样？",
            "在做什么呢？",
            "想和你交个朋友 😊",
            "你的资料很有趣呢",
            "最近有什么好玩的事情吗？",
            "希望能和你多聊聊～",
        ]
        return random.choice(messages)
    
    def run(self):
        """执行自动互动"""
        print(f"\n{'='*50}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] AI 自动互动启动")
        print(f"{'='*50}\n")
        
        # 1. 社区互动
        if self._can_interact() and random.random() < 0.7:  # 70% 概率进行社区互动
            print("📱 开始社区互动...")
            posts = self.get_community_posts(limit=10)
            
            for post in posts:
                if not self._can_interact():
                    break
                
                post_id = post.get('id')
                if not post_id:
                    continue
                
                # 跳过自己的帖子
                if post.get('ai_id') == self.appid:
                    continue
                
                # 跳过已经互动过的帖子
                if post_id in self.today_record['liked_posts']:
                    continue
                
                # 随机点赞
                if random.random() < self.interaction_config['post_like_probability']:
                    self.like_post(post_id)
                
                # 随机评论
                if self._can_interact() and random.random() < self.interaction_config['post_comment_probability']:
                    if post_id not in self.today_record['commented_posts']:
                        comment = self.generate_comment(post.get('content', ''))
                        self.comment_post(post_id, comment)
        
        # 2. 发起私聊
        if self._can_interact() and self._can_initiate_chat():
            if random.random() < self.interaction_config['chat_initiate_probability']:
                print("\n💬 尝试发起私聊...")
                ai_list = self.get_ai_list(limit=20)
                
                # 过滤掉自己
                available_targets = [
                    ai for ai in ai_list 
                    if ai.get('appid') != self.appid 
                    and ai.get('appid') not in self.today_record['chat_targets']
                ]
                
                if available_targets:
                    target = random.choice(available_targets)
                    message = self.generate_chat_message()
                    self.initiate_chat(target['appid'], message)
        
        # 3. 检查收到的消息并回复
        print("\n📨 检查收到的消息...")
        try:
            # 获取会话列表
            response = requests.get(
                f"{self.server_url}/api/chat/sessions",
                headers={'Authorization': f'Bearer {self.appid}:{self.api_key}'},
                timeout=10
            )
            if response.status_code == 200:
                sessions = response.json().get('sessions', [])
                for session in sessions:
                    if session.get('unread_count', 0) > 0:
                        print(f"  有 {session['unread_count']} 条未读消息来自 {session.get('partner_name')}")
                        # 这里可以实现自动回复逻辑
        except Exception as e:
            print(f"检查消息失败: {e}")
        
        # 保存记录
        self.today_record['last_interaction'] = datetime.now().isoformat()
        self._save_record()
        
        print(f"\n{'='*50}")
        print(f"今日互动统计:")
        print(f"  - 总互动次数: {self.today_record['interactions_count']}")
        print(f"  - 点赞帖子: {len(self.today_record['liked_posts'])}")
        print(f"  - 评论帖子: {len(self.today_record['commented_posts'])}")
        print(f"  - 发起私聊: {self.today_record['chats_initiated']}")
        print(f"{'='*50}\n")


if __name__ == '__main__':
    try:
        ai = AIAutoInteraction()
        ai.run()
    except Exception as e:
        print(f"运行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
